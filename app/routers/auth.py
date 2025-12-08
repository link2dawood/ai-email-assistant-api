# app/routers/auth.py - Complete Authentication Router with ALL Endpoints
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta
from bson import ObjectId
import secrets
import re
import logging

from app.config import settings
from app import database
from app.utils.auth import create_access_token, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============ Request/Response Models ============

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class SigninRequest(BaseModel):
    email: EmailStr
    password: str

class SocialSigninRequest(BaseModel):
    provider: str  # google, facebook, etc.
    token: str

class VerifyEmailRequest(BaseModel):
    token: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

# ============ Helper Functions ============

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def validate_password(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter"
        )
    if not re.search(r"[a-z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one lowercase letter"
        )
    if not re.search(r"\d", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one number"
        )
    return True

def generate_verification_token() -> str:
    """Generate random verification token"""
    return secrets.token_urlsafe(32)

# ============ Authentication Endpoints ============

@router.post("/signup")
async def signup(request: SignupRequest):
    """
    Register a new user with email and password
    """
    logger.info(f"Signup attempt for: {request.email}")
    
    try:
        # Check if user already exists
        existing_user = await database.users_collection.find_one({"email": request.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Validate password
        validate_password(request.password)
        
        # Generate verification token
        verification_token = generate_verification_token()
        
        # Create new user
        user_data = {
            "email": request.email,
            "name": request.name,
            "password_hash": hash_password(request.password),
            "email_verified": False,
            "verification_token": verification_token,
            "is_active": True,
            "subscription_plan": "free",
            "subscription_status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await database.users_collection.insert_one(user_data)
        user = await database.users_collection.find_one({"_id": result.inserted_id})
        
        # Create JWT token
        access_token = create_access_token({"sub": str(user["_id"])})
        
        logger.info(f"Signup successful for: {request.email}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user["_id"]),
                "email": user["email"],
                "name": user["name"],
                "email_verified": user["email_verified"],
                "subscription_plan": user["subscription_plan"],
                "subscription_status": user["subscription_status"],
                "profile_picture": user.get("profile_picture"),
                "created_at": user["created_at"]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}"
        )

@router.post("/signin")
async def signin(request: SigninRequest):
    """
    Sign in with email and password
    """
    logger.info(f"Signin attempt for: {request.email}")
    
    try:
        # Find user
        user = await database.users_collection.find_one({"email": request.email})
        if not user or "password_hash" not in user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(request.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Update last login
        await database.users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Create JWT token
        access_token = create_access_token({"sub": str(user["_id"])})
        
        logger.info(f"Signin successful for: {request.email}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user["_id"]),
                "email": user["email"],
                "name": user.get("name"),
                "email_verified": user.get("email_verified", False),
                "subscription_plan": user["subscription_plan"],
                "subscription_status": user["subscription_status"],
                "profile_picture": user.get("profile_picture"),
                "created_at": user["created_at"]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signin error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signin failed: {str(e)}"
        )

@router.post("/social")
async def social_signin(request: SocialSigninRequest):
    """
    Sign in with social provider (Google, Facebook, etc.)
    """
    logger.info(f"Social signin attempt with provider: {request.provider}")
    
    # TODO: Implement actual social login verification
    # For now, return a placeholder response
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Social login with {request.provider} not yet implemented"
    )

@router.post("/verify-email")
async def verify_email(request: VerifyEmailRequest):
    """
    Verify user email with token
    """
    logger.info("Email verification attempt")
    
    try:
        user = await database.users_collection.find_one({"verification_token": request.token})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        # Mark email as verified
        await database.users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "email_verified": True,
                    "verification_token": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Email verified for user: {user['email']}")
        
        return {"message": "Email verified successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )

@router.post("/resend-verification")
async def resend_verification(request: ResendVerificationRequest):
    """
    Resend verification email
    """
    logger.info(f"Resend verification request for: {request.email}")
    
    try:
        user = await database.users_collection.find_one({"email": request.email})
        
        # Don't reveal if email exists
        if not user:
            return {"message": "If the email exists, a verification link has been sent"}
        
        if user.get("email_verified"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )
        
        # Generate new token
        verification_token = generate_verification_token()
        
        await database.users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"verification_token": verification_token}}
        )
        
        # TODO: Send verification email
        logger.info(f"Verification email resent to: {request.email}")
        logger.info(f"Verification token: {verification_token}")
        
        return {"message": "Verification email sent"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resend verification error: {str(e)}")
        return {"message": "If the email exists, a verification link has been sent"}

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """
    Request password reset email
    """
    logger.info(f"Forgot password request for: {request.email}")
    
    try:
        user = await database.users_collection.find_one({"email": request.email})
        
        # Don't reveal if email exists
        if not user:
            return {"message": "If the email exists, a password reset link has been sent"}
        
        # Generate reset token
        reset_token = generate_verification_token()
        reset_expires = datetime.utcnow() + timedelta(hours=1)
        
        await database.users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "reset_token": reset_token,
                    "reset_token_expires": reset_expires
                }
            }
        )
        
        # TODO: Send password reset email
        logger.info(f"Password reset email sent to: {request.email}")
        logger.info(f"Reset token: {reset_token}")
        
        return {"message": "Password reset email sent"}
    
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """
    Reset password with token
    """
    logger.info("Password reset attempt")
    
    try:
        user = await database.users_collection.find_one({
            "reset_token": request.token,
            "reset_token_expires": {"$gt": datetime.utcnow()}
        })
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Validate new password
        validate_password(request.new_password)
        
        # Update password
        await database.users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "password_hash": hash_password(request.new_password),
                    "reset_token": None,
                    "reset_token_expires": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Password reset successful for user: {user['email']}")
        
        return {"message": "Password reset successful"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user = Depends(get_current_user)
):
    """
    Change password for authenticated user
    """
    logger.info(f"Password change request for user: {current_user['email']}")
    
    try:
        # Verify old password
        if not verify_password(request.old_password, current_user.get("password_hash", "")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Validate new password
        validate_password(request.new_password)
        
        # Update password
        await database.users_collection.update_one(
            {"_id": current_user["_id"]},
            {
                "$set": {
                    "password_hash": hash_password(request.new_password),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Password changed successfully for user: {current_user['email']}")
        
        return {"message": "Password changed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

@router.get("/google")
async def google_login():
    """
    Initiate Google OAuth flow
    """
    logger.info("Google OAuth URL requested")
    
    scopes = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify"
    ]
    
    scope_string = " ".join(scopes)
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.google_client_id}&"
        f"redirect_uri={settings.google_redirect_uri}&"
        f"response_type=code&"
        f"scope={scope_string}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    return {"auth_url": auth_url}

@router.get("/google/callback")
async def google_callback(code: str):
    """
    Handle Google OAuth callback
    """
    logger.info("Google OAuth callback received")
    
    # TODO: Implement actual Google OAuth callback
    # This requires exchanging the code for tokens and creating/updating user
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google OAuth callback not yet fully implemented"
    )

@router.get("/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    """
    Get current user information
    """
    return {
        "id": str(current_user["_id"]),
        "email": current_user["email"],
        "name": current_user.get("name"),
        "email_verified": current_user.get("email_verified", False),
        "subscription_plan": current_user.get("subscription_plan", "free"),
        "subscription_status": current_user.get("subscription_status", "active"),
        "profile_picture": current_user.get("profile_picture"),
        "created_at": current_user.get("created_at")
    }

@router.post("/logout")
async def logout(current_user = Depends(get_current_user)):
    """
    Logout user (client should delete token)
    """
    logger.info(f"Logout for user: {current_user['email']}")
    return {"message": "Logged out successfully"}