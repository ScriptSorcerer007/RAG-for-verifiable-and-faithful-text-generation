from pymongo import MongoClient
from django.conf import settings

MONGO_URI = "mongodb+srv://kuldeepsinghcsaiml24_db_user:OEo72N8tYs9vk7vi@cluster0.gsk50x2.mongodb.net/rag_db?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)

db = client["rag_db"]
documents_collection = db["documents"]