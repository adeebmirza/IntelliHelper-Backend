from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from typing import List

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

class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    formatted_content: Optional[str] = None


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    formatted_content: Optional[str] = None


class NoteResponse(BaseModel):
    id: str  # This will be assigned `note_id`
    title: str
    content: str
    formatted_content: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


class TaskCreate(BaseModel):
    task: str
    group: Optional[str] = "General"

class TaskUpdate(BaseModel):
    task: str
    group: str


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    model: str = "llama-3.3-70b-versatile"

class ModelListResponse(BaseModel):
    models: List[str]