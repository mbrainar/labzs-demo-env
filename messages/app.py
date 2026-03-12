from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from datetime import datetime, timezone

app = Flask(__name__)

# In-memory store for messages
messages = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Message Board</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f0f2f5;
            min-height: 100vh;
            padding: 2rem;
        }

        /* ── Top bar ── */
        .topbar {
            position: fixed;
            top: 0; left: 0; right: 0;
            height: 48px;
            background: #1a1a2e;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding: 0 1.5rem;
            z-index: 1000;
        }

        /* ── Admin dropdown ── */
        .admin-menu { position: relative; }
        .admin-btn {
            background: transparent;
            border: 1px solid rgba(255,255,255,0.25);
            color: #ccc;
            border-radius: 6px;
            padding: 0.3rem 0.85rem;
            font-size: 0.85rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.4rem;
            transition: border-color 0.2s, color 0.2s;
            margin-top: 0;
        }
        .admin-btn:hover { border-color: #fff; color: #fff; background: transparent; }
        .admin-btn svg { width: 14px; height: 14px; fill: currentColor; }

        .dropdown {
            display: none;
            position: absolute;
            right: 0;
            top: calc(100% + 8px);
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
            min-width: 180px;
            overflow: hidden;
        }
        .dropdown.open { display: block; }
        .dropdown-header {
            padding: 0.5rem 1rem;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #999;
            background: #f8f8f8;
            border-bottom: 1px solid #eee;
        }
        .dropdown a {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.65rem 1rem;
            color: #333;
            text-decoration: none;
            font-size: 0.9rem;
            transition: background 0.15s;
        }
        .dropdown a:hover { background: #f5f5f5; }
        .dropdown a.danger { color: #d93025; }
        .dropdown a.danger:hover { background: #fff0ef; }
        .dropdown a svg { width: 14px; height: 14px; fill: currentColor; flex-shrink: 0; }

        /* ── Modal confirm ── */
        .modal-overlay {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.45);
            z-index: 2000;
            align-items: center;
            justify-content: center;
        }
        .modal-overlay.open { display: flex; }
        .modal {
            background: white;
            border-radius: 12px;
            padding: 1.75rem;
            max-width: 360px;
            width: 90%;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        }
        .modal h3 { font-size: 1.1rem; color: #1a1a2e; margin-bottom: 0.5rem; }
        .modal p { font-size: 0.9rem; color: #666; margin-bottom: 1.25rem; }
        .modal-actions { display: flex; gap: 0.75rem; justify-content: flex-end; }
        .btn-cancel {
            background: #f0f0f0;
            color: #333;
            border: none;
            border-radius: 7px;
            padding: 0.5rem 1.1rem;
            font-size: 0.9rem;
            cursor: pointer;
            margin-top: 0;
        }
        .btn-cancel:hover { background: #e0e0e0; }
        .btn-confirm-clear {
            background: #d93025;
            color: white;
            border: none;
            border-radius: 7px;
            padding: 0.5rem 1.1rem;
            font-size: 0.9rem;
            cursor: pointer;
            margin-top: 0;
        }
        .btn-confirm-clear:hover { background: #b52a20; }

        /* ── Main content ── */
        .container {
            max-width: 700px;
            margin: 0 auto;
            padding-top: 4rem;
        }
        h1 { color: #1a1a2e; margin-bottom: 1.5rem; font-size: 1.8rem; }
        .post-form {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 2rem;
        }
        textarea {
            width: 100%;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 0.75rem;
            font-size: 1rem;
            resize: vertical;
            min-height: 100px;
            font-family: inherit;
            transition: border-color 0.2s;
        }
        textarea:focus { outline: none; border-color: #4f8ef7; }
        button[type=submit] {
            margin-top: 0.75rem;
            background: #4f8ef7;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.6rem 1.4rem;
            font-size: 1rem;
            cursor: pointer;
            transition: background 0.2s;
        }
        button[type=submit]:hover { background: #3a7bd5; }
        .messages h2 { color: #333; margin-bottom: 1rem; font-size: 1.2rem; }
        .message-card {
            background: white;
            border-radius: 10px;
            padding: 1rem 1.25rem;
            margin-bottom: 0.75rem;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06);
            border-left: 4px solid #4f8ef7;
        }
        .message-text { color: #222; font-size: 1rem; white-space: pre-wrap; word-break: break-word; }
        .message-ts { color: #888; font-size: 0.78rem; margin-top: 0.4rem; }
        .empty { color: #aaa; font-style: italic; text-align: center; padding: 2rem 0; }
    </style>
</head>
<body>

    <!-- Top bar with admin menu -->
    <div class="topbar">
        <div class="admin-menu" id="adminMenu">
            <button class="admin-btn" onclick="toggleDropdown()">
                <svg viewBox="0 0 24 24"><path d="M12 15.5A3.5 3.5 0 018.5 12 3.5 3.5 0 0112 8.5a3.5 3.5 0 013.5 3.5 3.5 3.5 0 01-3.5 3.5m7.43-2.92c.04-.36.07-.73.07-1.08s-.03-.73-.07-1.08l2.32-1.82c.21-.16.27-.45.13-.69l-2.2-3.81c-.13-.24-.42-.32-.65-.24l-2.74 1.1c-.57-.44-1.18-.8-1.86-1.07l-.42-2.92A.558.558 0 0014 2h-4c-.27 0-.5.19-.54.45l-.42 2.92c-.68.27-1.29.63-1.86 1.07L4.44 5.34c-.24-.09-.52 0-.65.24L1.59 9.39c-.14.24-.08.53.13.69l2.32 1.82C4.03 12.27 4 12.63 4 13s.03.73.07 1.08L1.72 15.9c-.21.16-.27.45-.13.69l2.2 3.81c.13.24.42.32.65.24l2.74-1.1c.57.44 1.18.8 1.86 1.07l.42 2.92c.04.26.27.45.54.45h4c.27 0 .5-.19.54-.45l.42-2.92c.68-.27 1.29-.63 1.86-1.07l2.74 1.1c.24.09.52 0 .65-.24l2.2-3.81c.14-.24.08-.53-.13-.69l-2.32-1.82z"/></svg>
                Admin
            </button>
            <div class="dropdown" id="dropdown">
                <div class="dropdown-header">Admin Actions</div>
                <a href="#" class="danger" onclick="openClearModal(); return false;">
                    <svg viewBox="0 0 24 24"><path d="M19 4h-3.5l-1-1h-5l-1 1H5v2h14M6 19a2 2 0 002 2h8a2 2 0 002-2V7H6v12z"/></svg>
                    Clear all messages
                </a>
            </div>
        </div>
    </div>

    <!-- Confirm clear modal -->
    <div class="modal-overlay" id="clearModal">
        <div class="modal">
            <h3>Clear all messages?</h3>
            <p>This will permanently delete all posted messages. This action cannot be undone.</p>
            <div class="modal-actions">
                <button class="btn-cancel" onclick="closeClearModal()">Cancel</button>
                <form method="POST" action="/admin/clear" style="margin:0">
                    <button type="submit" class="btn-confirm-clear">Yes, clear all</button>
                </form>
            </div>
        </div>
    </div>

    <div class="container">
        <h1>📋 Message Board</h1>
        <div class="post-form">
            <form method="POST" action="/">
                <textarea name="text" placeholder="Type your message here..." required></textarea>
                <br>
                <button type="submit">Post Message</button>
            </form>
        </div>
        <div class="messages">
            <h2>Posted Messages</h2>
            {% if messages %}
                {% for msg in messages|reverse %}
                <div class="message-card">
                    <div class="message-text">{{ msg.text }}</div>
                    <div class="message-ts">🕐 {{ msg.timestamp }}</div>
                </div>
                {% endfor %}
            {% else %}
                <p class="empty">No messages yet. Be the first to post!</p>
            {% endif %}
        </div>
    </div>

    <script>
        function toggleDropdown() {
            document.getElementById('dropdown').classList.toggle('open');
        }
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!document.getElementById('adminMenu').contains(e.target)) {
                document.getElementById('dropdown').classList.remove('open');
            }
        });
        function openClearModal() {
            document.getElementById('dropdown').classList.remove('open');
            document.getElementById('clearModal').classList.add('open');
        }
        function closeClearModal() {
            document.getElementById('clearModal').classList.remove('open');
        }
        // Close modal on overlay click
        document.getElementById('clearModal').addEventListener('click', function(e) {
            if (e.target === this) closeClearModal();
        });
    </script>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if text:
            messages.append({
                "text": text,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            })
    return render_template_string(HTML_TEMPLATE, messages=messages)


@app.route("/admin/clear", methods=["POST"])
def admin_clear():
    messages.clear()
    return redirect(url_for("index"))


@app.route("/api/messages", methods=["GET"])
def api_get_messages():
    return jsonify({"messages": messages})


@app.route("/api/messages", methods=["POST"])
def api_post_message():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Field 'text' is required and cannot be empty."}), 400
    entry = {
        "text": text,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    }
    messages.append(entry)
    return jsonify({"message": "Message posted successfully.", "data": entry}), 201


@app.route("/api/messages", methods=["DELETE"])
def api_clear_messages():
    messages.clear()
    return jsonify({"message": "All messages cleared."}), 200


if __name__ == "__main__":
    from threading import Thread
    import logging

    log = logging.getLogger("werkzeug")
    log.setLevel(logging.INFO)

    def run_web():
        app.run(host="0.0.0.0", port=8000)

    def run_api():
        app.run(host="0.0.0.0", port=9000)

    Thread(target=run_web, daemon=True).start()
    Thread(target=run_api).start()
