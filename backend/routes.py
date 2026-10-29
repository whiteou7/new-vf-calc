from io import BytesIO

from flask import Blueprint, jsonify, request, send_file

from lib import generate_b50_image

api = Blueprint("api", __name__)


@api.get("/health")
def health():
    return jsonify({"status": "soumd voltex"}), 200


@api.post("/api/generate-b50")
def generate():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Expected JSON body"}), 400
    try:
        img = generate_b50_image(data)
        buf = BytesIO()
        img.save(buf, format="PNG", optimize=True)
        buf.seek(0)
        return send_file(buf, mimetype="image/png", download_name="b50.png")
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
