import csv
import io
import ipaddress
import os
import re
from urllib.parse import urlparse

from flask import Flask, Response, abort, jsonify, redirect, render_template, request, url_for
from sqlalchemy import delete, select

from models import CheckIn, db, utcnow

API_KEY = os.environ.get("API_KEY", "").strip()
STALE_MINUTES = int(os.environ.get("STALE_AFTER_MINUTES", "10"))
MAX_CHECKINS_PER_DEVICE = int(os.environ.get("MAX_CHECKINS_PER_DEVICE", "300"))
DB_PATH = os.environ.get("DB_PATH", "/data/iot.db")
PER_PAGE = 25


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        db.create_all()

    register_routes(app)
    return app


def humanize_delta(delta_seconds: float) -> str:
    if delta_seconds < 0:
        delta_seconds = 0
    seconds = int(delta_seconds)
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        remaining_minutes = minutes % 60
        return f"{hours}h {remaining_minutes}m ago"
    days = hours // 24
    remaining_hours = hours % 24
    return f"{days}d {remaining_hours}h ago"


def valid_ipv4(value):
    """Returns the normalized IPv4 string, or None. Check-in data is client-supplied,
    so anything used to build an SSH link or .rdp file must pass through this."""
    try:
        return str(ipaddress.IPv4Address(value))
    except ValueError:
        return None


def latest_checkin(hostname):
    return (
        CheckIn.query.filter_by(hostname=hostname)
        .order_by(CheckIn.received_at.desc(), CheckIn.id.desc())
        .first()
    )


def safe_filename(hostname):
    return re.sub(r"[^A-Za-z0-9._-]", "_", hostname)


def csv_safe(value):
    """Neutralize spreadsheet formula injection; check-in fields are client-supplied."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


def require_same_origin():
    """Blocks cross-site form posts to the destructive endpoints (the app has no login)."""
    origin = request.headers.get("Origin")
    if origin and urlparse(origin).netloc != request.host:
        abort(403, description="Cross-origin request blocked")


def prune_old_checkins(hostname):
    """Keep only the newest MAX_CHECKINS_PER_DEVICE rows for this device."""
    keep = (
        select(CheckIn.id)
        .where(CheckIn.hostname == hostname)
        .order_by(CheckIn.received_at.desc(), CheckIn.id.desc())
        .limit(MAX_CHECKINS_PER_DEVICE)
    )
    db.session.execute(
        delete(CheckIn)
        .where(CheckIn.hostname == hostname, CheckIn.id.not_in(keep))
        .execution_options(synchronize_session=False)
    )


def latest_checkins():
    """One row per hostname, most recent checkin only."""
    subq = (
        db.session.query(
            CheckIn.hostname, db.func.max(CheckIn.received_at).label("max_received")
        )
        .group_by(CheckIn.hostname)
        .subquery()
    )
    rows = (
        db.session.query(CheckIn)
        .join(
            subq,
            db.and_(
                CheckIn.hostname == subq.c.hostname,
                CheckIn.received_at == subq.c.max_received,
            ),
        )
        .order_by(CheckIn.hostname.asc())
        .all()
    )
    return rows


def serialize_device_row(row: CheckIn):
    now = utcnow()
    age = (now - row.received_at).total_seconds()
    return {
        "hostname": row.hostname,
        "ip_address": row.ip_address,
        "device_time": row.device_time_raw,
        "received_at": row.received_at.isoformat() + "Z",
        "time_since": humanize_delta(age),
        "age_seconds": age,
        "online": age <= STALE_MINUTES * 60,
    }


def register_routes(app: Flask):
    @app.get("/")
    def dashboard():
        rows = latest_checkins()
        devices = [serialize_device_row(r) for r in rows]
        return render_template(
            "dashboard.html",
            devices=devices,
            stale_minutes=STALE_MINUTES,
            deleted=request.args.get("deleted"),
        )

    @app.get("/api/devices")
    def api_devices():
        rows = latest_checkins()
        return jsonify([serialize_device_row(r) for r in rows])

    @app.get("/device/<hostname>")
    def device_detail(hostname):
        page = request.args.get("page", 1, type=int)
        query = (
            CheckIn.query.filter_by(hostname=hostname)
            .order_by(CheckIn.received_at.desc())
        )
        pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)
        if pagination.total == 0:
            abort(404, description=f"No check-ins found for host '{hostname}'")
        checkins = [
            {
                "ip_address": c.ip_address,
                "device_time": c.device_time_raw,
                "received_at": c.received_at.isoformat() + "Z",
                "time_since": humanize_delta((utcnow() - c.received_at).total_seconds()),
            }
            for c in pagination.items
        ]
        latest = latest_checkin(hostname)
        return render_template(
            "device.html",
            hostname=hostname,
            checkins=checkins,
            pagination=pagination,
            device_ip=valid_ipv4(latest.ip_address),
            cleared=request.args.get("cleared", type=int),
        )

    @app.get("/device/<hostname>/rdp")
    def device_rdp(hostname):
        latest = latest_checkin(hostname)
        if latest is None:
            abort(404, description=f"No check-ins found for host '{hostname}'")
        ip = valid_ipv4(latest.ip_address)
        if ip is None:
            abort(400, description="Latest check-in has no valid IPv4 address")
        filename = safe_filename(hostname) + ".rdp"
        body = f"full address:s:{ip}\r\nprompt for credentials:i:1\r\n"
        return Response(
            body,
            mimetype="application/x-rdp",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.get("/device/<hostname>/history.csv")
    def device_history_csv(hostname):
        rows = (
            CheckIn.query.filter_by(hostname=hostname)
            .order_by(CheckIn.received_at.desc(), CheckIn.id.desc())
            .all()
        )
        if not rows:
            abort(404, description=f"No check-ins found for host '{hostname}'")
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["hostname", "ip_address", "device_time", "received_at_utc"])
        for r in rows:
            writer.writerow(
                [
                    csv_safe(r.hostname),
                    csv_safe(r.ip_address),
                    csv_safe(r.device_time_raw),
                    r.received_at.isoformat() + "Z",
                ]
            )
        filename = safe_filename(hostname) + "-checkins.csv"
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.post("/device/<hostname>/clear")
    def device_clear(hostname):
        """Deletes all but the newest check-in, so the device stays on the dashboard."""
        require_same_origin()
        latest = latest_checkin(hostname)
        if latest is None:
            abort(404, description=f"No check-ins found for host '{hostname}'")
        result = db.session.execute(
            delete(CheckIn)
            .where(CheckIn.hostname == hostname, CheckIn.id != latest.id)
            .execution_options(synchronize_session=False)
        )
        db.session.commit()
        return redirect(
            url_for("device_detail", hostname=hostname, cleared=result.rowcount), code=303
        )

    @app.post("/device/<hostname>/delete")
    def device_delete(hostname):
        require_same_origin()
        result = db.session.execute(
            delete(CheckIn)
            .where(CheckIn.hostname == hostname)
            .execution_options(synchronize_session=False)
        )
        db.session.commit()
        if result.rowcount == 0:
            abort(404, description=f"No check-ins found for host '{hostname}'")
        return redirect(url_for("dashboard", deleted=hostname), code=303)

    @app.post("/api/checkin")
    def api_checkin():
        if API_KEY:
            supplied = request.headers.get("X-API-Key", "")
            if supplied != API_KEY:
                abort(401, description="Invalid or missing X-API-Key header")

        data = request.get_json(silent=True) or request.form
        if not hasattr(data, "get"):
            abort(400, description="Request body must be a JSON object or form data")
        hostname = (data.get("hostname") or "").strip()
        ip_address = (data.get("ip_address") or request.remote_addr or "").strip()
        device_time_raw = (data.get("device_time") or "").strip()

        if not hostname:
            abort(400, description="Field 'hostname' is required")
        if not ip_address:
            abort(400, description="Field 'ip_address' is required")
        if not device_time_raw:
            abort(400, description="Field 'device_time' is required")

        checkin = CheckIn(
            hostname=hostname,
            ip_address=ip_address,
            device_time_raw=device_time_raw,
            received_at=utcnow(),
        )
        db.session.add(checkin)
        db.session.flush()
        prune_old_checkins(hostname)
        db.session.commit()

        return jsonify({"status": "ok", "checkin": checkin.to_dict()}), 201

    @app.errorhandler(400)
    @app.errorhandler(401)
    @app.errorhandler(403)
    @app.errorhandler(404)
    def handle_error(err):
        return jsonify({"error": err.description}), err.code


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
