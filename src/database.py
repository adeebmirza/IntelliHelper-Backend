from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# MongoDB Connection
MONGO_URI = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URI)
db = client["fastapi_auth"]
users_collection = db["users"]
otp_collection = db["otp_verifications"] 
login_activity_collection = db["login_activity"]


# Helper function: Get user from DB (by username or email)
async def get_user(username: str = None, email: str = None):
    query = {}
    if username:
        query["username"] = username
    if email:
        query["email"] = email
    return await users_collection.find_one(query)

async def save_login_activity(login_data : dict):
    await login_activity_collection.insert_one(login_data)