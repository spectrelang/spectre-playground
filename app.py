from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from runner import run_spectre

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/compile", methods=["POST"])
@app.route("/api/run", methods=["POST"])
def run():
    data = request.get_json(silent=True)

    if not data or "code" not in data:
        return jsonify({"error": "No code provided"}), 400

    code = data["code"]
    output_file = data.get("output", None)
    flags = data.get("flags", [])

    try:
        result = run_spectre(code, output_file, flags)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
