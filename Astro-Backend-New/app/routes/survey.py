from flask import Blueprint, request, jsonify
from models.user import User

survey_bp = Blueprint("survey", __name__)

@survey_bp.route("/survey", methods=["POST"])
def create_survey():
    """
    Endpoint to create survey data for a user.
    Expected payload: JSON with phone and survey data.
    """
    data = request.get_json()

    if not data or "phone" not in data or "survey" not in data:
        return jsonify({"error": "Phone number and survey data are required"}), 400

    phone = data["phone"]
    survey_data = data["survey"]

    try:
        User.add_survey(phone, survey_data)
        return jsonify({"message": "Survey created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@survey_bp.route("/survey", methods=["PUT"])
def update_survey():
    """
    Endpoint to update survey data for a user.
    Expected payload: JSON with phone and updated survey fields.
    """
    data = request.get_json()

    if not data or "phone" not in data or "survey" not in data:
        return jsonify({"error": "Phone number and updated survey data are required"}), 400

    phone = data["phone"]
    updated_data = data["survey"]

    try:
        User.update_survey(phone, updated_data)
        return jsonify({"message": "Survey updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
