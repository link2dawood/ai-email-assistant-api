from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta
from src.prisma.models import (
    UserCreate, UserLogin, UserUpdate, SocialSigninRequest, 
    ForgotPasswordRequest, ResetPasswordRequest
)
from src.auth.auth_service import auth_service
from src.prisma.database import get_db
from src.config import settings
import logging

# Setup Logger
logger = logging.getLogger("AuthAPI")
router = APIRouter()

# --- GOOGLE AUTH ENDPOINTS ---

@router.get("/google")
async def google_login():
    """Generates the Google OAuth link using the URI from .env"""
    import urllib.parse
    
    scope = "openid email profile https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.compose https://www.googleapis.com/auth/gmail.send"
    
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": scope,
        "access_type": "offline",
        "prompt": "consent"
    }
    
    query_string = urllib.parse.urlencode(params)
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"
    
    return {"auth_url": auth_url}

import httpx

# ...

@router.post("/google/callback")
async def google_callback(payload: dict):
    """
    Receives the code from Frontend and swaps it for a token.
    Then fetches real user info from Google.
    """
    code = payload.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Code is required")

    # 1. Exchange Code for Token
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.google_redirect_uri,
    }

    async with httpx.AsyncClient() as client:
        token_res = await client.post(token_url, data=token_data)
        
    if token_res.status_code != 200:
        logger.error(f"Google Token Error: {token_res.text}")
        raise HTTPException(status_code=400, detail="Failed to retrieve Google token")

    tokens = token_res.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")  # Get refresh token for long-term access
    expires_in = tokens.get("expires_in", 3600)  # Default to 1 hour if not provided
    
    # Calculate token expiration time
    token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    # 2. Fetch User Info
    user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    async with httpx.AsyncClient() as client:
        user_res = await client.get(user_info_url, headers={"Authorization": f"Bearer {access_token}"})

    if user_res.status_code != 200:
        logger.error(f"Google User Info Error: {user_res.text}")
        raise HTTPException(status_code=400, detail="Failed to fetch Google user info")

    google_user = user_res.json()
    email = google_user.get("email")
    name = google_user.get("name")
    picture = google_user.get("picture")
    google_id = google_user.get("id")

    if not email:
        raise HTTPException(status_code=400, detail="Google account has no email")

    # 3. Find or Create User in DB
    db = get_db()
    
    user = await db.users.find_one({"email": email})
    
    # Prepare token data (only update refresh_token if we received one)
    token_data = {
        "google_access_token": access_token,
        "token_expires_at": token_expires_at
    }
    if refresh_token:
        token_data["google_refresh_token"] = refresh_token
    
    if not user:
        new_user = {
            "email": email,
            "name": name,
            "picture": picture,
            "created_at": datetime.utcnow(),
            "google_id": google_id,
            "plan": "free",
            **token_data
        }
        res = await db.users.insert_one(new_user)
        user_id = str(res.inserted_id)
    else:
        # Update existing user with latest info
        user_id = str(user["_id"])
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "google_id": google_id, 
                "picture": picture, 
                "name": name,
                **token_data
            }}
        )

    # 4. Generate App JWT
    token = auth_service.create_access_token({"sub": user_id})
    return {"access_token": token, "token_type": "bearer"}

# --- STANDARD AUTH ENDPOINTS ---

@router.post("/signup")
async def signup(user_data: UserCreate):
    try:
        db = get_db()
        # Check if email exists
        if await db.users.find_one({"email": user_data.email}):
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        new_user = user_data.dict()
        new_user["password_hash"] = auth_service.get_password_hash(new_user.pop("password"))
        new_user["created_at"] = datetime.utcnow()
        
        res = await db.users.insert_one(new_user)
        
        return {
            "id": str(res.inserted_id),
            "email": user_data.email,
            "message": "User created successfully"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Signup Error: {e}")
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")

@router.post("/signin")
async def signin(creds: UserLogin):
    db = get_db()
    user = await db.users.find_one({"email": creds.email})
    
    if not user or not auth_service.verify_password(creds.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = auth_service.create_access_token({"sub": str(user["_id"])})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
async def get_current_user(user = Depends(auth_service.get_current_user)):
    """Return the current authenticated user"""
    return {
        "id": str(user["_id"]),
        "name": user.get("name"),
        "email": user["email"],
        "plan": user.get("plan", "free"),
        "picture": user.get("picture") # If available from Google
    }

@router.put("/me")
async def update_current_user(
    update_data: UserUpdate,
    user = Depends(auth_service.get_current_user)
):
    """Update displayed name or picture"""
    db = get_db()
    
    update_fields = {}
    if update_data.name is not None:
        update_fields["name"] = update_data.name
    if update_data.picture is not None:
        update_fields["picture"] = update_data.picture
        
    if not update_fields:
        return {"message": "No changes provided"}
        
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": update_fields}
    )
    
    return {"message": "Profile updated successfully"}

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    db = get_db()
    user = await db.users.find_one({"email": request.email})
    if not user:
        # Don't reveal if user exists or not for security, but for MVP we can just return success
        return {"message": "If the email exists, a reset link has been sent."}

    # Generate reset token
    reset_token = auth_service.generate_random_token()
    reset_token_expires = datetime.utcnow() + timedelta(minutes=30) # 30 mins expiry

    # Save to DB
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "reset_token": reset_token,
            "reset_token_expires": reset_token_expires
        }}
    )

    # Mock Email Sending
    # In production, use aiosmtplib to send real email
    reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
    logger.info(f"============ PASSWORD RESET LINK ============")
    logger.info(f"To: {request.email}")
    logger.info(f"Link: {reset_link}")
    logger.info(f"============================================")

    return {"message": "If the email exists, a reset link has been sent."}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    db = get_db()
    
    # Find user with this token
    user = await db.users.find_one({
        "reset_token": request.token,
        "reset_token_expires": {"$gt": datetime.utcnow()} # Check expiry
    })

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    # Hash new password
    new_hash = auth_service.get_password_hash(request.new_password)

    # Update user
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"password_hash": new_hash}, "$unset": {"reset_token": "", "reset_token_expires": ""}}
    )

    return {"message": "Password has been reset successfully. You can now login with your new password."}