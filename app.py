import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, UTC
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

mongo_client = MongoClient(os.getenv("MONGODB_URI"))
db = mongo_client["bahl_ai"]
conversations = db["conversations"]


# Create new conversation
@app.route("/new-chat", methods=["POST"])
def new_chat():
    chat_count = conversations.count_documents({})
    title = f"Chat {chat_count + 1}"

    convo = {
        "title": title,
        "createdAt": datetime.now(UTC),
        "messages": []
    }

    result = conversations.insert_one(convo)
    return jsonify({
        "conversationId": str(result.inserted_id),
        "title": title
    })


# Get all conversations
@app.route("/conversations", methods=["GET"])
def list_conversations():
    convos = conversations.find().sort("createdAt", -1)

    return jsonify([
        {
            "id": str(c["_id"]),
            "title": c["title"]
        }
        for c in convos
    ])


# Load one conversation
@app.route("/conversation/<id>", methods=["GET"])
def load_conversation(id):
    convo = conversations.find_one({"_id": ObjectId(id)})

    if not convo:
        return jsonify({"error": "Not found"}), 404

    return jsonify({
        "id": str(convo["_id"]),
        "title": convo["title"],
        "messages": convo["messages"]
    })


# Rename conversation
@app.route("/conversation/<id>/rename", methods=["PUT"])
def rename_conversation(id):
    new_title = request.json.get("title")

    conversations.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"title": new_title}}
    )

    return jsonify({"success": True})


# Delete conversation
@app.route("/conversation/<id>", methods=["DELETE"])
def delete_conversation(id):
    conversations.delete_one({"_id": ObjectId(id)})
    return jsonify({"success": True})


# Chat endpoint
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data["message"]
    conversation_id = data["conversationId"]

    conversations.update_one(
        {"_id": ObjectId(conversation_id)},
        {
            "$push": {
                "messages": {
                    "role": "user",
                    "content": message,
                    "timestamp": datetime.now(UTC)
                }
            }
        }
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are Bahl AI."},
            {"role": "user", "content": message}
        ]
    )

    reply = response.choices[0].message.content

    conversations.update_one(
        {"_id": ObjectId(conversation_id)},
        {
            "$push": {
                "messages": {
                    "role": "bot",
                    "content": reply,
                    "timestamp": datetime.now(UTC)
                }
            }
        }
    )

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True)