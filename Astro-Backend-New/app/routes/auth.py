from flask import Blueprint, request, jsonify
from models.user import User
from utils.jwt import create_jwt_token

from utils.otp import generate_otp, send_otp
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    if not data or not all(k in data for k in ("name", "phone")):
        return jsonify({"error": "Missing required fields"}), 400

    if User.find_by_phone(data["phone"]):
        return jsonify({"error": "User already exists"}), 400

    user = User.create_user(data["name"], data["phone"])
   
    return jsonify({"message": "User created successfully"}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or "phone" not in data:
        return jsonify({"error": "Missing phone field"}), 400

    user = User.find_by_phone(data["phone"])
    if user:
        token = create_jwt_token(data["phone"])
        return jsonify({"token": token}), 200
    return jsonify({"error": "User not found"}), 404


@auth_bp.route("/send-otp", methods=["POST"])
def send_otp_route():
    data = request.get_json()
    if not data or not all(k in data for k in ("name", "phone")):
        return jsonify({"error": "Missing required fields"}), 400

    otp = generate_otp()
    if send_otp(data["name"], data["phone"], otp):
        User.save_otp(data["phone"], otp)
        return jsonify({"message": "OTP sent successfully"}), 200
    return jsonify({"error": "Failed to send OTP"}), 500

@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp_route():
    data = request.get_json()
    if not data or not all(k in data for k in ("phone", "otp")):
        return jsonify({"error": "Missing required fields"}), 400

    if User.verify_otp(data["phone"], data["otp"]):
        token = create_jwt_token(data["phone"])
        return jsonify({"message": "OTP verified successfully", "token": token}), 200
    return jsonify({"error": "Invalid OTP"}), 400
