# app/models.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId


# ===================== ObjectId Support =====================
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


# ===================== User Models =====================
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None


class UserCreate(UserBase):
    google_id: Optional[str] = None
    outlook_id: Optional[str] = None
    password: Optional[str] = None  # added from first file


class UserInDB(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    google_id: Optional[str] = None
    outlook_id: Optional[str] = None
    password_hash: Optional[str] = None

    # OAuth
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None

    # Verification
    email_verified: bool = False
    verification_token: Optional[str] = None
    reset_token: Optional[str] = None
    reset_token_expires: Optional[datetime] = None

    # Profile
    profile_picture: Optional[str] = None
    last_login: Optional[datetime] = None
    is_active: bool = True

    # Subscription
    subscription_plan: str = "free"
    subscription_status: str = "active"
    stripe_customer_id: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class User(UserBase):
    id: str
    subscription_plan: str
    subscription_status: str
    profile_picture: Optional[str] = None
    created_at: datetime


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ===================== Token Models =====================
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None


# ===================== Email Thread Models =====================
class EmailThreadBase(BaseModel):
    subject: Optional[str] = None
    importance: int = 0
    category: Optional[str] = None  # client, lead, invoice, misc


class EmailThreadCreate(EmailThreadBase):
    user_id: str
    thread_id: str
    last_message_at: datetime


class EmailThreadInDB(EmailThreadCreate):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class EmailThread(EmailThreadBase):
    id: str
    thread_id: str
    last_message_at: datetime
    created_at: datetime


# ===================== Email Models =====================
class EmailBase(BaseModel):
    sender: str
    sender_email: EmailStr
    recipients: List[EmailStr]
    cc: Optional[List[EmailStr]] = []
    bcc: Optional[List[EmailStr]] = []
    subject: str
    body: str
    html_body: Optional[str] = None
    date: datetime
    snippet: Optional[str] = None


class EmailCreate(EmailBase):
    thread_id: str
    gmail_id: str
    attachments: List[dict] = []

    # AI fields
    ai_summary: Optional[str] = None
    ai_reply: Optional[str] = None
    ai_category: Optional[str] = None
    ai_importance: Optional[int] = None
    ai_sentiment: Optional[str] = None


class EmailInDB(EmailCreate):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    is_read: bool = False
    is_starred: bool = False
    labels: List[str] = []
    received_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Email(EmailBase):
    id: str
    gmail_id: str
    ai_summary: Optional[str] = None
    ai_reply: Optional[str] = None
    ai_category: Optional[str] = None
    ai_importance: Optional[int] = None
    ai_sentiment: Optional[str] = None
    date: datetime


class EmailRequest(BaseModel):
    limit: int = Field(default=50, le=100)
    skip: int = 0
    category: Optional[str] = None
    is_read: Optional[bool] = None


class EmailResponse(BaseModel):
    id: str
    sender: str
    sender_email: EmailStr
    subject: str
    body: str
    received_at: datetime
    is_read: bool
    is_starred: bool
    category: Optional[str] = None
    ai_summary: Optional[str] = None


# ===================== AI Models =====================
class EmailClassifyRequest(BaseModel):
    email_id: str
    email_content: str


class EmailClassifyResponse(BaseModel):
    category: str
    confidence: float
    summary: str
    sentiment: str


class EmailReplyRequest(BaseModel):
    email_id: str
    email_content: str
    tone: str = "professional"


class EmailReplyResponse(BaseModel):
    reply_text: str
    confidence: float


class AIClassifyRequest(BaseModel):
    email_body: str
    subject: Optional[str] = None


class AIClassifyResponse(BaseModel):
    category: str
    importance: int
    summary: str


class AIReplyRequest(BaseModel):
    email_body: str
    subject: Optional[str] = None
    tone: str = "professional"


class AIReplyResponse(BaseModel):
    reply: str


# ===================== Reminder Models =====================
class ReminderBase(BaseModel):
    email_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: datetime
    priority: str = "medium"


class ReminderCreate(ReminderBase):
    user_id: str


class ReminderInDB(ReminderCreate):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    is_completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Reminder(ReminderBase):
    id: str
    is_completed: bool
    created_at: datetime


# ===================== Billing Models =====================
class BillingPlan(BaseModel):
    name: str
    price: float
    features: List[str]
    stripe_price_id: str


class CheckoutSessionRequest(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseModel):
    session_id: str
    url: str


class SubscriptionResponse(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    stripe_subscription_id: str
    tier: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool

    class Config:
        populate_by_name = True


# ===================== Utility =====================
class EmailSyncRequest(BaseModel):
    limit: int = 50


class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EmailListResponse(BaseModel):
    emails: List[EmailThread]
    total: int
    page: int
    limit: int
