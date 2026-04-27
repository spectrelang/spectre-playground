from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from runner import SecurityViolation, run_spectre

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

    if not isinstance(data, dict) or "code" not in data:
        return jsonify({"error": "No code provided"}), 400

    code = data["code"]
    if not isinstance(code, str) or not code.strip():
        return jsonify({"error": "Code must be a non-empty string"}), 400

    output_file = data.get("output")
    flags = data.get("flags", [])

    if output_file not in (None, ""):
        return jsonify({"error": "Custom output paths are not allowed"}), 400

    if not isinstance(flags, list):
        return jsonify({"error": "Flags must be a list"}), 400

    if flags:
        return jsonify({"error": "Custom compiler flags are not allowed"}), 400

    try:
        result = run_spectre(code, output_file, flags)
        return jsonify(result)
    except SecurityViolation as e:
        return jsonify({
            "error": str(e)
        }), 400
    except FileNotFoundError as e:
        return jsonify({
            "error": str(e)
        }), 500
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
