"""
Email Management Router
Handles email operations: fetch, send, sync, etc.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import datetime
from bson import ObjectId
import logging

from app import database
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# ============ Request/Response Models ============

class EmailSendRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    cc: list[EmailStr] = []
    bcc: list[EmailStr] = []

class EmailListResponse(BaseModel):
    id: str
    from_email: str
    to: str
    subject: str
    body: str
    received_at: datetime
    is_read: bool
    labels: list[str] = []

class DraftSaveRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    cc: list[EmailStr] = []
    bcc: list[EmailStr] = []

# ============ Email Endpoints ============

@router.get("/")
async def list_emails(
    skip: int = 0,
    limit: int = 20,
    current_user = Depends(get_current_user)
):
    """
    List user emails with pagination
    """
    logger.info(f"Listing emails for user: {current_user['email']}")
    
    try:
        # Query emails for the user
        emails = await database.emails_collection.find(
            {"user_id": current_user["_id"]}
        ).sort("received_at", -1).skip(skip).limit(limit).to_list(limit)
        
        # Count total emails
        total = await database.emails_collection.count_documents(
            {"user_id": current_user["_id"]}
        )
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "emails": [
                {
                    "id": str(email["_id"]),
                    "from_email": email.get("from_email"),
                    "to": email.get("to"),
                    "subject": email.get("subject"),
                    "body": email.get("body", "")[:200],  # Preview
                    "received_at": email.get("received_at"),
                    "is_read": email.get("is_read", False),
                    "labels": email.get("labels", [])
                }
                for email in emails
            ]
        }
    
    except Exception as e:
        logger.error(f"Error listing emails: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list emails"
        )

@router.get("/{email_id}")
async def get_email(
    email_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get single email details
    """
    logger.info(f"Fetching email: {email_id}")
    
    try:
        email = await database.emails_collection.find_one({
            "_id": ObjectId(email_id),
            "user_id": current_user["_id"]
        })
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found"
            )
        
        # Mark as read
        await database.emails_collection.update_one(
            {"_id": email["_id"]},
            {"$set": {"is_read": True}}
        )
        
        return {
            "id": str(email["_id"]),
            "from_email": email.get("from_email"),
            "to": email.get("to"),
            "subject": email.get("subject"),
            "body": email.get("body"),
            "received_at": email.get("received_at"),
            "is_read": True,
            "labels": email.get("labels", []),
            "attachments": email.get("attachments", [])
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch email"
        )

@router.post("/send")
async def send_email(
    request: EmailSendRequest,
    current_user = Depends(get_current_user)
):
    """
    Send an email
    """
    logger.info(f"Sending email from {current_user['email']} to {request.to}")
    
    try:
        email_data = {
            "user_id": current_user["_id"],
            "from_email": current_user["email"],
            "to": request.to,
            "cc": request.cc,
            "bcc": request.bcc,
            "subject": request.subject,
            "body": request.body,
            "status": "sent",
            "sent_at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        
        result = await database.emails_collection.insert_one(email_data)
        
        logger.info(f"Email sent successfully: {result.inserted_id}")
        
        return {
            "message": "Email sent successfully",
            "email_id": str(result.inserted_id)
        }
    
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email"
        )

@router.post("/draft")
async def save_draft(
    request: DraftSaveRequest,
    current_user = Depends(get_current_user)
):
    """
    Save email as draft
    """
    logger.info(f"Saving draft for user: {current_user['email']}")
    
    try:
        draft_data = {
            "user_id": current_user["_id"],
            "from_email": current_user["email"],
            "to": request.to,
            "cc": request.cc,
            "bcc": request.bcc,
            "subject": request.subject,
            "body": request.body,
            "status": "draft",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await database.drafts_collection.insert_one(draft_data)
        
        logger.info(f"Draft saved: {result.inserted_id}")
        
        return {
            "message": "Draft saved successfully",
            "draft_id": str(result.inserted_id)
        }
    
    except Exception as e:
        logger.error(f"Error saving draft: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save draft"
        )

@router.post("/sync")
async def sync_emails(
    current_user = Depends(get_current_user)
):
    """
    Sync emails from Gmail
    """
    logger.info(f"Syncing emails for user: {current_user['email']}")
    
    try:
        # TODO: Implement Gmail API integration
        
        return {
            "message": "Email sync started",
            "emails_synced": 0,
            "status": "pending"
        }
    
    except Exception as e:
        logger.error(f"Error syncing emails: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync emails"
        )

@router.delete("/{email_id}")
async def delete_email(
    email_id: str,
    current_user = Depends(get_current_user)
):
    """
    Delete an email
    """
    logger.info(f"Deleting email: {email_id}")
    
    try:
        result = await database.emails_collection.delete_one({
            "_id": ObjectId(email_id),
            "user_id": current_user["_id"]
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found"
            )
        
        logger.info(f"Email deleted: {email_id}")
        
        return {"message": "Email deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete email"
        )