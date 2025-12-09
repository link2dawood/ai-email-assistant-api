# FILE: src/auth/auth_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta
from src.prisma.models import (
    UserCreate, UserLogin, SocialSigninRequest, 
    VerifyEmailRequest, ResendVerificationRequest,
    ForgotPasswordRequest, ResetPasswordRequest
)
from src.auth.auth_service import auth_service
from src.prisma.database import get_db

router = APIRouter()

# 1. SIGNUP
@router.post("/signup")
async def signup(user_data: UserCreate):
    db = get_db()
    if await db.users.find_one({"email": user_data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = user_data.dict()
    new_user["password_hash"] = auth_service.get_password_hash(new_user.pop("password"))
    new_user["created_at"] = datetime.utcnow()
    new_user["email_verified"] = False
    new_user["verification_token"] = auth_service.generate_random_token()
    
    res = await db.users.insert_one(new_user)
    
    # In a real app, send email here using new_user["verification_token"]
    
    return {
        "id": str(res.inserted_id),
        "email": user_data.email,
        "message": "User created. Please verify your email."
    }

# 2. SIGNIN
@router.post("/signin")
async def signin(creds: UserLogin):
    db = get_db()
    user = await db.users.find_one({"email": creds.email})
    
    if not user or not auth_service.verify_password(creds.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = auth_service.create_access_token({"sub": str(user["_id"])})
    return {"access_token": token, "token_type": "bearer", "user": {"email": user["email"], "name": user.get("name")}}

# 3. SOCIAL SIGNIN (Placeholder logic)
@router.post("/social")
async def social_signin(req: SocialSigninRequest):
    # Here you would verify the token with Google/Facebook API
    # For now, we simulate a successful login
    return {"message": f"Social login with {req.provider} not fully configured yet, but endpoint works."}

# 4. VERIFY EMAIL
@router.post("/verify-email")
async def verify_email(req: VerifyEmailRequest):
    db = get_db()
    user = await db.users.find_one({"verification_token": req.token})
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
        
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"email_verified": True, "verification_token": None}}
    )
    return {"message": "Email verified successfully"}

# 5. RESEND VERIFICATION
@router.post("/resend-verification")
async def resend_verification(req: ResendVerificationRequest):
    db = get_db()
    user = await db.users.find_one({"email": req.email})
    
    if user and not user.get("email_verified"):
        new_token = auth_service.generate_random_token()
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"verification_token": new_token}}
        )
        # Mock sending email
        print(f"Sending verification email to {req.email} with token: {new_token}")
        
    return {"message": "If the email exists, a verification link has been sent."}

# 6. FORGOT PASSWORD
@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    db = get_db()
    user = await db.users.find_one({"email": req.email})
    
    if user:
        reset_token = auth_service.generate_random_token()
        # Set token with expiration (e.g., 1 hour from now)
        expires = datetime.utcnow() + timedelta(hours=1)
        
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"reset_token": reset_token, "reset_expires": expires}}
        )
        # Mock sending email
        print(f"Sending reset email to {req.email} with token: {reset_token}")

    return {"message": "If the email exists, a reset link has been sent."}

# 7. RESET PASSWORD
@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    db = get_db()
    
    # Find user with valid token and check expiration
    user = await db.users.find_one({
        "reset_token": req.token,
        "reset_expires": {"$gt": datetime.utcnow()} # Check if expiry time is in the future
    })
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
    new_hash = auth_service.get_password_hash(req.new_password)
    
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"password_hash": new_hash, "reset_token": None, "reset_expires": None}}
    )
    
    return {"message": "Password has been reset successfully."}