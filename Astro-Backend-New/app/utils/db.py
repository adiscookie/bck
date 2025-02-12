from pymongo import MongoClient

def get_db():
    client = MongoClient("mongodb+srv://dave:drishti123@dave.qhoyz.mongodb.net/Supermind?retryWrites=true&w=majority&appName=Dave")
    return client["Supermind"]

