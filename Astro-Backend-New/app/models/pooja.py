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


class Pooja:
    @staticmethod
    def create_booking(user, pujari, pooja, price, timing, date):
        db = get_db()
        booking = {
            "user": {"name": user["name"], "phone": user["phone"]},
            "pujari": {
                "name": pujari["name"],
                "phone": pujari["phone"],
                "address": pujari["address"]
            },
            "pooja": pooja,
            "price": price,
            "timing": timing,
            "date": date,
        }
        result = db.bookings.insert_one(booking)
        booking["_id"] = str(result.inserted_id)  # Convert ObjectId to string
        return booking

    @staticmethod
    def update_booking(booking_id, updated_data):
        db = get_db()
        result = db.bookings.update_one({"_id": ObjectId(booking_id)}, {"$set": updated_data})
        if result.matched_count == 0:
            return None
        return serialize_mongo_doc(db.bookings.find_one({"_id": ObjectId(booking_id)}))

    @staticmethod
    def find_booking_by_id(booking_id):
        db = get_db()
        booking = db.bookings.find_one({"_id": ObjectId(booking_id)})
        return serialize_mongo_doc(booking)
