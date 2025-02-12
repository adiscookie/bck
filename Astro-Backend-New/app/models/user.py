from utils.db import get_db

class User:
    @staticmethod
    def create_user(name, phone):
        db = get_db()
        user = {"name": name, "phone": phone}
        db.users.insert_one(user)
        return user

    @staticmethod
    def find_by_phone(phone):
        db = get_db()
        return db.users.find_one({"phone": phone})

    @staticmethod
    def save_otp(phone, otp):
        db = get_db()
        db.otps.update_one({"phone": phone}, {"$set": {"otp": otp}}, upsert=True)

    @staticmethod
    def verify_otp(phone, otp):
        db = get_db()
        record = db.otps.find_one({"phone": phone})
        return record and record.get("otp") == otp

    # New methods for survey-related functionality
    @staticmethod
    def add_survey(phone, survey_data):
        """
        Adds survey data to the user's profile.

        :param phone: User's phone number to identify the user.
        :param survey_data: A dictionary containing the survey fields.
        """
        db = get_db()
        db.users.update_one(
            {"phone": phone},
            {"$set": {"survey": survey_data}},
            upsert=True
        )

    @staticmethod
    def update_survey(phone, updated_data):
        """
        Updates existing survey data for the user.

        :param phone: User's phone number to identify the user.
        :param updated_data: A dictionary containing updated survey fields.
        """
        db = get_db()
        db.users.update_one(
            {"phone": phone},
            {"$set": {"survey": updated_data}}
        )

    @staticmethod
    def get_survey(phone):
        """
        Retrieves survey data of the user.

        :param phone: User's phone number to identify the user.
        :return: Survey data if exists, None otherwise.
        """
        db = get_db()
        user = db.users.find_one({"phone": phone})
        return user.get("survey") if user else None

    @staticmethod
    def delete_survey(phone):
        """
        Deletes the survey data for the user.

        :param phone: User's phone number to identify the user.
        """
        db = get_db()
        db.users.update_one(
            {"phone": phone},
            {"$unset": {"survey": ""}}
        )
