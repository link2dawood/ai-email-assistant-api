# FILE: src/prisma/models.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    picture: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# --- NEW AUTH MODELS ---
class SocialSigninRequest(BaseModel):
    provider: str
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
# -----------------------

class EmailCreate(BaseModel):
    to: EmailStr
    subject: str
    body: str

class ReminderCreate(BaseModel):
    title: str
    due_date: datetime

class AIRequest(BaseModel):
    text: str
    tone: Optional[str] = "professional"