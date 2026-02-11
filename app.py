import os
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from openai import OpenAI
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

load_dotenv()

app = Flask(__name__)

# OpenAI setup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# MongoDB setup
mongo_client = MongoClient(os.getenv("MONGODB_URI"))
db = mongo_client["bahl_ai"]
conversations = db["conversations"]


@app.route("/")
def home():
    return render_template("index.html")


# Create new conversation
@app.route("/new-chat", methods=["POST"])
def new_chat():
    convo = {
        "title": "New Chat",
        "createdAt": datetime.utcnow(),
        "messages": []
    }
    result = conversations.insert_one(convo)
    return jsonify({"conversationId": str(result.inserted_id)})


# Get all conversations (for sidebar)
@app.route("/conversations", methods=["GET"])
def list_conversations():
    convos = conversations.find().sort("createdAt", -1)
    return jsonify([
        {
            "id": str(c["_id"]),
            "title": c.get("title", "New Chat")
        }
        for c in convos
    ])


# Get a specific conversation
@app.route("/conversation/<id>", methods=["GET"])
def load_conversation(id):
    convo = conversations.find_one({"_id": ObjectId(id)})

    if not convo:
        return jsonify({"error": "Conversation not found"}), 404

    return jsonify({
        "id": str(convo["_id"]),
        "messages": convo.get("messages", [])
    })


# Send message
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data["message"]
    conversation_id = data["conversationId"]

    # Save user message
    conversations.update_one(
        {"_id": ObjectId(conversation_id)},
        {
            "$push": {
                "messages": {
                    "role": "user",
                    "content": message,
                    "timestamp": datetime.utcnow()
                }
            }
        }
    )

    # Call OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are Bahl AI, a helpful assistant."},
            {"role": "user", "content": message}
        ]
    )

    reply = response.choices[0].message.content

    # Save bot reply
    conversations.update_one(
        {"_id": ObjectId(conversation_id)},
        {
            "$push": {
                "messages": {
                    "role": "bot",
                    "content": reply,
                    "timestamp": datetime.utcnow()
                }
            }
        }
    )

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True)
