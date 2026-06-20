"""Flask backend – exposes POST /api/generate-b50 → PNG image."""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from generate import generate_b50_image
from io import BytesIO

app = Flask(__name__)
CORS(app)          # allow requests from the Vite dev server


@app.route("/api/generate-b50", methods=["POST"])
def generate():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Expected JSON body"}), 400
    try:
        img = generate_b50_image(data)
        buf = BytesIO()
        img.save(buf, format="PNG", optimize=True,)
        buf.seek(0)
        return send_file(buf, mimetype="image/png", download_name="b50.png")
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    print("B50 image backend → http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
