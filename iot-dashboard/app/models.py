from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    """Naive datetime, but always in UTC.

    SQLite's DATETIME type does not actually persist tzinfo (SQLAlchemy's
    SQLite dialect formats it via strftime and reads it back naive), so an
    aware `received_at` written to the DB comes back naive on the next
    query. Keeping every stored timestamp naive-but-UTC from the start
    avoids ever subtracting an aware datetime from a naive one.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CheckIn(db.Model):
    __tablename__ = "checkins"

    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(255), nullable=False, index=True)
    ip_address = db.Column(db.String(64), nullable=False)
    device_time_raw = db.Column(db.String(64), nullable=True)
    received_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "device_time": self.device_time_raw,
            "received_at": self.received_at.isoformat() + "Z",
        }
