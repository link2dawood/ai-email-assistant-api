from fastapi import APIRouter, Depends, HTTPException
from src.auth.auth_service import auth_service
from src.email.email_service import email_service
from src.gmail.gmail_service import gmail_service
from src.prisma.models import EmailCreate
from src.prisma.database import get_db

router = APIRouter()

# List all emails for the current user
@router.get("/")
async def list_emails(
    filter: str = "all",
    current_user = Depends(auth_service.get_current_user)
):
    """
    List emails with optional filtering.
    Filters: all, inbox, starred, snoozed, sent, drafts, archive, spam, trash, purchases, important
    """
    from bson import ObjectId
    from datetime import datetime
    
    # Build query based on filter
    query = {"user_id": current_user["_id"]}
    
    if filter == "inbox" or filter == "all":
        query["folder"] = "inbox"
    elif filter == "starred":
        query["is_starred"] = True
    elif filter == "snoozed":
        query["folder"] = "snoozed"
        # Only show if snooze time has not passed
        query["snoozed_until"] = {"$gt": datetime.utcnow()}
    elif filter == "sent":
        query["folder"] = "sent"
    elif filter == "drafts":
        query["folder"] = "drafts"
    elif filter == "archive":
        query["folder"] = "archive"
    elif filter == "spam":
        query["folder"] = "spam"
    elif filter == "trash":
        query["folder"] = "trash"
    elif filter == "purchases":
        query["ai_category"] = "Purchases"
    elif filter == "important":
        query["ai_importance"] = {"$gte": 7}
    
    # Fetch emails from database
    db = get_db()
    cursor = db.emails.find(query).sort("_id", -1).limit(100)
    emails = await cursor.to_list(length=100)
    
    # Convert ObjectId to str for response
    for email in emails:
        email["id"] = str(email.pop("_id"))
        if "user_id" in email:
            email["user_id"] = str(email["user_id"])
    
    return emails

@router.post("/send")
async def send_email(
    email: EmailCreate, 
    current_user = Depends(auth_service.get_current_user)
):
    try:
        # Use Gmail Service to send real email
        result = await gmail_service.send_email(
            current_user, 
            email.to, 
            email.subject, 
            email.body
        )
        
        # Save to DB as well
        email_id = await email_service.create_email(current_user["_id"], email)
        
        return {"message": "Email sent successfully", "id": email_id, "gmail_id": result.get("id")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))