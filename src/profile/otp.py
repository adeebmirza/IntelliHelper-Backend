from src.database import otp_collection, users_collection
from datetime import datetime, timedelta
from fastapi import HTTPException
from src.profile.password import get_password_hash
from src.profile.form import UserSignup
from logger import logger

async def store_otp_in_db(user: UserSignup, otp: str):
    """Stores OTP and user details in the database for verification."""
    otp_data = {
        "email": user.email,
        "otp": otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=10),
        "name": user.name,
        "username": user.username,
        "gender": user.gender,
        "dob": user.dob,
        "password": get_password_hash(user.password),
    }
    await otp_collection.insert_one(otp_data)


async def get_latest_otp(email: str):
    """Fetches the latest OTP entry for a given email."""
    return await otp_collection.find_one({"email": email}, sort=[("expires_at", -1)])

# Helper function: Validate OTP
async def validate_otp(otp_entry, user_otp: str):
    """Validates the OTP and checks expiration."""
    if not otp_entry:
        raise HTTPException(status_code=400, detail="No OTP found for this email")

    current_time = datetime.utcnow()
    expires_at = otp_entry["expires_at"]

    # Ensure proper datetime comparison
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)

    logger.info(f"Current time: {current_time}, OTP expires at: {expires_at}")

    if current_time > expires_at:
        await otp_collection.delete_one({"email": otp_entry['email']})
        raise HTTPException(status_code=400, detail="OTP expired. Request a new one.")

    if otp_entry["otp"] != user_otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

# Helper function: Register User
async def register_user(otp_entry):
    """Registers a new user in the database."""
    user_data = {
        "name": otp_entry["name"],
        "username": otp_entry["username"],
        "email": otp_entry["email"],
        "gender": otp_entry["gender"],
        "dob": otp_entry["dob"],
        "password": otp_entry["password"]
    }
    await users_collection.insert_one(user_data)
    await otp_collection.delete_one({"email": otp_entry["email"]})