import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INBOX = os.path.join(BASE_DIR, "hermes_inbox.txt")
OUTBOX = os.path.join(BASE_DIR, "hermes_outbox.txt")


@app.route("/hermes", methods=["POST"])
def hermes_inbox():
    data = request.get_json(silent=True)
    if not data or "prompt" not in data:
        return jsonify({"error": "Wymagane pole: prompt"}), 400

    prompt = data["prompt"]
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] PROMPT:\n{prompt}\n{'─' * 60}\n"

    with open(INBOX, "a", encoding="utf-8") as f:
        f.write(entry)

    return jsonify({"status": "ok", "timestamp": timestamp}), 200


@app.route("/hermes/outbox", methods=["GET"])
def hermes_outbox():
    if not os.path.exists(OUTBOX):
        return Response("", mimetype="text/plain; charset=utf-8")
    with open(OUTBOX, "r", encoding="utf-8") as f:
        content = f.read()
    return Response(content, mimetype="text/plain; charset=utf-8")


@app.route("/hermes/outbox", methods=["DELETE"])
def hermes_clear_outbox():
    with open(OUTBOX, "w", encoding="utf-8") as f:
        f.write("")
    return jsonify({"status": "cleared"}), 200


@app.route("/hermes/inbox", methods=["GET"])
def hermes_inbox_read():
    if not os.path.exists(INBOX):
        return Response("", mimetype="text/plain; charset=utf-8")
    with open(INBOX, "r", encoding="utf-8") as f:
        content = f.read()
    return Response(content, mimetype="text/plain; charset=utf-8")


@app.route("/hermes/inbox", methods=["DELETE"])
def hermes_clear_inbox():
    with open(INBOX, "w", encoding="utf-8") as f:
        f.write("")
    return jsonify({"status": "cleared"}), 200


@app.route("/hermes/status", methods=["GET"])
def hermes_status():
    inbox_size = os.path.getsize(INBOX) if os.path.exists(INBOX) else 0
    outbox_size = os.path.getsize(OUTBOX) if os.path.exists(OUTBOX) else 0
    return jsonify({
        "status": "alive",
        "inbox_bytes": inbox_size,
        "outbox_bytes": outbox_size,
        "inbox_exists": os.path.exists(INBOX),
        "outbox_exists": os.path.exists(OUTBOX),
    }), 200


if __name__ == "__main__":
    for path in (INBOX, OUTBOX):
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                pass
    app.run(host="0.0.0.0", port=5000, debug=False)