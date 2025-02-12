from flask import Blueprint, request, jsonify
from models.pooja import Pooja

pooja_bp = Blueprint("pooja", __name__)

@pooja_bp.route("/pooja", methods=["POST"])
def create_pooja_booking():
    data = request.get_json()

    # Validate request payload
    if not data or "user" not in data or "pujari" not in data or "pooja" not in data or \
            "price" not in data or "timing" not in data or "date" not in data:
        return jsonify({"error": "Invalid data. Please provide all required fields."}), 400

    user = data["user"]
    pujari = data["pujari"]
    pooja = data["pooja"]
    price = data["price"]
    timing = data["timing"]
    date = data["date"]

    # Ensure required fields are present in user and pujari objects
    if not user.get("name") or not user.get("phone"):
        return jsonify({"error": "User name and phone are required"}), 400

    if not pujari.get("name") or not pujari.get("phone") or not pujari.get("address"):
        return jsonify({"error": "Pujari name, phone, and address are required"}), 400

    try:
        booking = Pooja.create_booking(user, pujari, pooja, price, timing, date)
        return jsonify({"message": "Pooja booking created successfully", "data": booking}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@pooja_bp.route("/pooja/<booking_id>", methods=["PUT"])
def update_pooja_booking(booking_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "No update data provided"}), 400

    try:
        updated_booking = Pooja.update_booking(booking_id, data)
        if not updated_booking:
            return jsonify({"error": "Booking not found"}), 404
        return jsonify({"message": "Pooja booking updated successfully", "data": updated_booking}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
