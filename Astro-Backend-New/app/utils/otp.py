import requests
import random
from utils.db import get_db

def generate_otp():
    return random.randint(100000, 999999)

def send_otp(name, phone, otp):
    try:
        response = requests.post(
            "https://backend.aisensy.com/campaign/t1/api/v2",
            json={
                "apiKey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY3NjJjNzYyNDgzMWUxMGMxMWM0MTI4OSIsIm5hbWUiOiJIZXkgQmhhZ3dhbiIsImFwcE5hbWUiOiJBaVNlbnN5IiwiY2xpZW50SWQiOiI2NzFhNGNmNDViNTE0ZTBiZmNjYmEzMWQiLCJhY3RpdmVQbGFuIjoiRlJFRV9GT1JFVkVSIiwiaWF0IjoxNzM0NTI2ODE4fQ.qX1wNylNmJr0kI-v1aA9wWCIqomcB4zSKUJRgyIwqrE",
                "campaignName": "OTP verification campaign",
                "destination": phone,
                "userName": name,
                "templateParams": [f"{otp}"],
                "source": "backend",
            }
        )

        # Check if response is successful (status code 200)
        if response.status_code == 200:
            response_json = response.json()

            # Check for success field in the response
            if response_json.get("success") == 'true':
                return True
            else:
                print(f"Error from AISensy API: {response_json}")
                return False
        else:
            # Log the response if the status code is not 200
            print(f"Error: Received status code {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print("Error sending OTP:", e)
        return False
