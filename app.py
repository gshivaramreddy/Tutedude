import os
import json
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "flask_form_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "submissions")

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

mongo_client = None
def get_db():
    global mongo_client
    if mongo_client is None:
        if not MONGODB_URI:
            raise RuntimeError("MONGODB_URI is not set. See .env")
        mongo_client = MongoClient(MONGODB_URI)
    return mongo_client[DB_NAME]

@app.route("/api", methods=["GET"])
def api():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return jsonify(list(data.values()))
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "data.json not found"}), 500
    except json.JSONDecodeError:
        return jsonify({"error": "data.json is not valid JSON"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def index():
    return send_from_directory("static", "index.html")

@app.route("/submit", methods=["POST"])
def submit():
    try:
        payload = request.get_json()
        if not payload:
            return {"success": False, "error": "Invalid JSON payload"}, 400

        name = payload.get("name", "").strip()
        email = payload.get("email", "").strip()
        message = payload.get("message", "").strip()

        if not name or not email:
            return {"success": False, "error": "Name and email are required"}, 400

        db = get_db()
        doc = {"name": name, "email": email, "message": message}
        result = db[COLLECTION_NAME].insert_one(doc)
        return {"success": True, "id": str(result.inserted_id)}, 201

    except RuntimeError as re:
        return {"success": False, "error": str(re)}, 500
    except Exception as e:
        return {"success": False, "error": str(e)}, 500

@app.route("/success", methods=["GET"])
def success_page():
    return send_from_directory("static", "success.html")


@app.route("/submittodoitem", methods=["POST"])
def submit_todo_item():
    """
    Accepts JSON or form data:
      - itemName
      - itemDescription
    Stores into MongoDB collection 'todos' (creates DB connection using get_db()).
    """
    try:
        data = request.get_json(silent=True) or request.form or {}
        item_name = (data.get("itemName") or data.get("item_name") or "").strip()
        item_desc = (data.get("itemDescription") or data.get("item_description") or "").strip()
        if not item_name:
            return {"success": False, "error": "itemName is required"}, 400
        db = get_db()
        todo = {"itemName": item_name, "itemDescription": item_desc}
        result = db.get_collection("todos").insert_one(todo)
        return {"success": True, "inserted_id": str(result.inserted_id)}, 201
    except RuntimeError as re:
        return {"success": False, "error": str(re)}, 500
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))