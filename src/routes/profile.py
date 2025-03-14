from fastapi import APIRouter, HTTPException, Depends
from src.database import get_user, users_collection
from src.profile.token_jwt import generate_reset_token, verify_reset_token
from src.profile.password import get_password_hash, verify_password
from src.profile.email_service import send_forget
from src.profile.form import ForgotPasswordRequest, ResetPasswordForm, UpdateProfileRequest
from src.profile.token_jwt import get_current_user


profile_router = APIRouter(tags=["profile"])


@profile_router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    user = await users_collection.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email")

    token = generate_reset_token(request.email) 
    send_forget(request.email, token)

    return {"message": "Password reset email sent. Check your inbox."}




# Reset Password
@profile_router.post("/reset-password/{token}")
async def reset_password(token: str, form_data: ResetPasswordForm):
    email = verify_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    # Hash new password and update
    hashed_password = get_password_hash(form_data.new_password)
    await users_collection.update_one({"email": email}, {"$set": {"password": hashed_password}})

    return {"message": "Password successfully reset. You can now log in."}

# Profile Route - Fetch User Profile
@profile_router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Fetches the profile information of the authenticated user.
    """
    return {
        "name": current_user["name"],
        "username": current_user["username"],
        "email": current_user["email"],
        "gender": current_user["gender"],
        "dob": current_user["dob"],
    }



# Update Profile Route
@profile_router.put("/profile/update")
async def update_profile(update_data: UpdateProfileRequest, current_user: dict = Depends(get_current_user)):
    """
    Updates the profile information of the authenticated user.
    """
    update_fields = {key: value for key, value in update_data.dict().items() if value is not None}

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Check if the new username already exists (if updated)
    if "username" in update_fields:
        existing_user = await get_user(username=update_fields["username"])
        if existing_user and existing_user["email"] != current_user["email"]:
            raise HTTPException(status_code=400, detail="Username already taken")

    # Handle password update
    if "new_password" in update_fields:
        if "current_password" not in update_fields:
            raise HTTPException(status_code=400, detail="Current password is required to change password")

        # Verify current password
        if not verify_password(update_fields["current_password"], current_user["password"]):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Hash and update the new password
        update_fields["password"] = get_password_hash(update_fields["new_password"])
        del update_fields["new_password"]
        del update_fields["current_password"]

    # Update the user record
    await users_collection.update_one({"email": current_user["email"]}, {"$set": update_fields})

    return {"message": "Profile updated successfully"}