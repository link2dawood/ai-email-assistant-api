from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from src.prisma.models import UserCreate, UserLogin, SocialSigninRequest
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
    scope = "openid email profile https://www.googleapis.com/auth/gmail.readonly"
    
    # This uses the GOOGLE_REDIRECT_URI set in your .env file
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.google_client_id}&"
        f"redirect_uri={settings.google_redirect_uri}&"
        f"response_type=code&"
        f"scope={scope}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    return {"auth_url": auth_url}

@router.post("/google/callback")
async def google_callback(payload: dict):
    """
    Receives the code from Frontend and swaps it for a token.
    IMPORTANT: We must use the SAME redirect_uri used to generate the link.
    """
    code = payload.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Code is required")

    # MOCK LOGIN for MVP (Replace with real Google Token Exchange later)
    # Since we can't easily swap tokens without a real library setup, 
    # we assume if we got a code, the user authenticated on the frontend.
    
    # In a real production app, you would use `requests.post` to google here.
    
    mock_email = "google_user_mvp@example.com"
    db = get_db()
    
    # Find or Create User
    user = await db.users.find_one({"email": mock_email})
    if not user:
        new_user = {
            "email": mock_email,
            "name": "Google User",
            "created_at": datetime.utcnow(),
            "google_id": "mvp_google_id",
            "plan": "free"
        }
        res = await db.users.insert_one(new_user)
        user_id = str(res.inserted_id)
    else:
        user_id = str(user["_id"])

    # Generate JWT
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