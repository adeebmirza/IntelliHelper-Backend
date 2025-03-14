from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter, FastAPI
from src.profile.otp import store_otp_in_db, get_latest_otp, validate_otp, register_user
from src.profile.password import verify_password
from src.profile.email_service import send
from src.database import get_user,save_login_activity
from src.profile.form import UserSignup, OTPVerification, LoginRequest,LoginActivityRequest
from logger import logger
import pyotp
from src.profile.token_jwt import create_access_token, create_refresh_token,get_current_user

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/signup")
async def signup(user: UserSignup):
    logger.info(f"Signup request received for {user.email}")
    # Check if user already exists
    existing_user = await get_user(username=user.username) or await get_user(email=user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    # Generate a static OTP
    otp_secret = pyotp.random_base32()
    totp = pyotp.TOTP(otp_secret)
    otp = totp.now()  # Fixed OTP at signup time

    # Store OTP with expiration time (10 minutes)
    await store_otp_in_db(user, otp)

    # Send OTP via email
    send(user.email, otp)
    logger.info(f"OTP {otp} sent to {user.email}")

    return {"message": "OTP sent to your email. Please verify to complete registration within 10 minutes."}

# Verify OTP Route
@auth_router.post("/verify-otp")
async def verify_otp(data: OTPVerification):
    """Handles OTP verification and user registration."""
    logger.info(f"OTP verification request received for {data.email}")

    otp_entry = await get_latest_otp(data.email)
    await validate_otp(otp_entry, data.otp)
    await register_user(otp_entry)

    return {"message": "Registration successful! You can now log in."}

# Login Route (Accepting Username OR Email)
@auth_router.post("/login")
async def login(request: LoginRequest):
    # Fetch user from database using username or email
    user = await get_user(username=request.username_or_email) or await get_user(email=request.username_or_email)

    if not user or not verify_password(request.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user["username"]})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "name": user["name"],
            "username": user["username"],
            "email": user["email"],
            "gender": user["gender"],
            "dob": user["dob"],
        }
    }
#for swagger ui 
@auth_router.post("/login-form")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):  # FastAPI expects OAuth2PasswordRequestForm
    user = await get_user(username=form_data.username) or await get_user(email=form_data.username)

    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user["username"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@auth_router.post("/log-login-activity")
async def log_login_activity(activity_data: LoginActivityRequest):
    """Log user login activity (IP, Location, Device Type)"""
    
    await save_login_activity(activity_data.model_dump())

    return {"message": "Login activity logged successfully"}