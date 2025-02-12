from flask import Blueprint, request, jsonify
from models.pujari import Pujari
from utils.jwt import create_jwt_token
from utils.otp import generate_otp, send_otp

pujari_bp = Blueprint("pujari", __name__)

# Pujari Signup Route
@pujari_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    
    # Check if required fields are present
    if not data or not all(k in data for k in ("name", "phone", "address")):
        return jsonify({"error": "Missing required fields"}), 400

    # Check if the pujari already exists by phone number
    if Pujari.find_by_phone(data["phone"]):
        return jsonify({"error": "Pujari already exists"}), 400

    # Create pujari
    pujari = Pujari.create_pujari(data["name"], data["phone"], data["address"])
    return jsonify({"message": "Pujari created successfully", "data": pujari}), 201

# Pujari Login Route
@pujari_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    
    # Check if phone number is provided
    if not data or "phone" not in data:
        return jsonify({"error": "Missing phone field"}), 400

    # Find pujari by phone
    pujari = Pujari.find_by_phone(data["phone"])
    if pujari:
        # Generate JWT token if found
        token = create_jwt_token(data["phone"])
        return jsonify({"token": token}), 200
    return jsonify({"error": "Pujari not found"}), 404

# Send OTP Route for Pujari
@pujari_bp.route("/send-otp", methods=["POST"])
def send_otp_route():
    data = request.get_json()
    
    # Check if required fields are present
    if not data or not all(k in data for k in ("name", "phone")):
        return jsonify({"error": "Missing required fields"}), 400

    # Generate and send OTP
    otp = generate_otp()
    if send_otp(data["name"], data["phone"], otp):
        Pujari.save_otp(data["phone"], otp)
        return jsonify({"message": "OTP sent successfully"}), 200
    return jsonify({"error": "Failed to send OTP"}), 500

# Verify OTP Route for Pujari
@pujari_bp.route("/verify-otp", methods=["POST"])
def verify_otp_route():
    data = request.get_json()
    
    # Check if required fields are present
    if not data or not all(k in data for k in ("phone", "otp")):
        return jsonify({"error": "Missing required fields"}), 400

    # Verify OTP
    if Pujari.verify_otp(data["phone"], data["otp"]):
        # Generate JWT token upon successful verification
        token = create_jwt_token(data["phone"])
        return jsonify({"message": "OTP verified successfully", "token": token}), 200
    return jsonify({"error": "Invalid OTP"}), 400

# Create Pujari Route
@pujari_bp.route("/pujari", methods=["POST"])
def create_pujari():
    data = request.get_json()

    # Validate required fields
    if not data or "name" not in data or "phone" not in data or "address" not in data:
        return jsonify({"error": "Name, phone, and address are required"}), 400

    name = data["name"]
    phone = data["phone"]
    address = data["address"]

    try:
        pujari = Pujari.create_pujari(name, phone, address)
        return jsonify({"message": "Pujari created successfully", "data": pujari}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update Pujari Route
@pujari_bp.route("/pujari", methods=["PUT"])
def update_pujari():
    data = request.get_json()

    # Validate required fields
    if not data or "phone" not in data:
        return jsonify({"error": "Phone number is required"}), 400

    phone = data["phone"]
    updated_data = data.get("updated_data", {})

    if not updated_data:
        return jsonify({"error": "No updated data provided"}), 400

    try:
        updated_pujari = Pujari.update_pujari(phone, updated_data)
        if not updated_pujari:
            return jsonify({"error": "Pujari not found"}), 404
        return jsonify({"message": "Pujari updated successfully", "data": updated_pujari}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
