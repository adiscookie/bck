from bson import ObjectId
from utils.db import get_db


def serialize_mongo_doc(doc):
    """
    Helper function to convert ObjectId to string in a MongoDB document.
    """
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc


class Pujari:
    @staticmethod
    def create_pujari(name, phone, address):
        db = get_db()
        pujari = {"name": name, "phone": phone, "address": address}
        result = db.pujaris.insert_one(pujari)
        pujari["_id"] = str(result.inserted_id)  # Convert ObjectId to string
        return pujari

    @staticmethod
    def update_pujari(phone, updated_data):
        db = get_db()
        result = db.pujaris.update_one({"phone": phone}, {"$set": updated_data})
        if result.matched_count == 0:
            return None
        return serialize_mongo_doc(db.pujaris.find_one({"phone": phone}))

    @staticmethod
    def find_pujari_by_phone(phone):
        db = get_db()
        pujari = db.pujaris.find_one({"phone": phone})
        return serialize_mongo_doc(pujari)
    
    @staticmethod
    def save_otp(phone, otp):
        db = get_db()
        db.pujaris.update_one({"phone": phone}, {"$set": {"otp": otp}}, upsert=True)

    @staticmethod
    def verify_otp(phone, otp):
        db = get_db()
        pujari = db.pujaris.find_one({"phone": phone})
        return pujari and pujari.get("otp") == otp

