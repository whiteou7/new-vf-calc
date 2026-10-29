"""Flask backend: POST /api/generate-b50 -> PNG image."""

from flask import Flask
from flask_cors import CORS

from routes import api

app = Flask(__name__)
CORS(app)
app.register_blueprint(api)

if __name__ == "__main__":
    print("B50 image backend -> http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
