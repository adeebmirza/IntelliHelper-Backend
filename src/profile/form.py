from pydantic import BaseModel, Field, EmailStr
from typing import Optional

# User Model
class UserSignup(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    gender: str
    dob: str  # Date of Birth as a string (YYYY-MM-DD)
    password: str = Field(..., min_length=6)

# OTP Verification Model
class OTPVerification(BaseModel):
    email: EmailStr
    otp: str

# User Login Model (Accepts username OR email)
class LoginRequest(BaseModel):
    username_or_email: str
    password: str

# Reset Password Form
class ResetPasswordForm(BaseModel):
    new_password: str


# Update Profile Model
class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=6)


# Forgot Password Request
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class LoginActivityRequest(BaseModel):
    username: str
    email: str
    ip: str
    city: str
    country: str
    device_type: str