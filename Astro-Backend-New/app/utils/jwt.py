import jwt
from datetime import datetime, timedelta

def create_jwt_token(phone):
    payload = {
        "phone": phone,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    secret_key = "your_secret_key"
    return jwt.encode(payload, secret_key, algorithm="HS256")