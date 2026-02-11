import os
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["bahl_ai"]

conversations = db["conversations"]

def create_conversation():
    convo = {
        "title": "New Chat",
        "createdAt": datetime.utcnow(),
        "messages": []
    }
    result = conversations.insert_one(convo)
    return str(result.inserted_id)

def add_message(conversation_id, role, content):
    conversations.update_one(
        {"_id": ObjectId(conversation_id)},
        {
            "$push": {
                "messages": {
                    "role": role,
                    "content": content,
                    "timestamp": datetime.utcnow()
                }
            }
        }
    )

def get_conversations():
    return [
        {
            "id": str(c["_id"]),
            "title": c["title"]
        }
        for c in conversations.find().sort("createdAt", -1)
    ]

def get_conversation(conversation_id):
    convo = conversations.find_one({"_id": ObjectId(conversation_id)})
    convo["id"] = str(convo["_id"])
    del convo["_id"]
    return convo
