from fastapi import APIRouter, Depends
from src.auth.auth_service import auth_service
from src.gmail.gmail_service import gmail_service

router = APIRouter()

@router.post("/sync")
async def sync_gmail(current_user = Depends(auth_service.get_current_user)):
    from src.prisma.database import get_db
    from datetime import datetime
    
    # 1. Fetch from Google
    emails = await gmail_service.fetch_emails(current_user, max_results=20)
    
    if not emails:
        return {"status": "success", "count": 0, "message": "No new emails or failed fetch"}
        
    db = get_db()
    count = 0
    
    # 2. Save to DB
    for email_data in emails:
        # Check if exists
        existing = await db.emails.find_one({"gmail_id": email_data["gmail_id"], "user_id": current_user["_id"]})
        
        if not existing:
            new_email = {
                "user_id": current_user["_id"],
                "gmail_id": email_data["gmail_id"],
                "thread_id": email_data["thread_id"],
                "subject": email_data["subject"],
                "body": email_data["body"],
                "snippet": email_data["snippet"],
                "from_name": email_data["from_name"],
                "from_email": email_data["from"], # sender
                "received_at": email_data["received_at"], # Keep as string or parse
                "is_read": email_data["is_read"],
                "folder": "inbox",
                "ai_importance": 0, # Default, AI can update later
                "created_at": datetime.utcnow()
            }
            await db.emails.insert_one(new_email)
            count += 1
            
    return {"status": "success", "synced": count, "total_fetched": len(emails)}

@router.get("/stats")
async def get_stats(user = Depends(auth_service.get_current_user)):
    """
    Return statistics for the sidebar.
    Returns real counts from the database.
    """
    from src.prisma.database import get_db
    db = get_db()
    
    try:
        # Count emails in different folders
        inbox_count = await db.emails.count_documents({
            "user_id": user["_id"],
            "folder": "inbox",
            "is_read": False
        })
        
        purchases_count = await db.emails.count_documents({
            "user_id": user["_id"],
            "ai_category": "Purchases"
        })
        
        spam_count = await db.emails.count_documents({
            "user_id": user["_id"],
            "folder": "spam"
        })
        
        trash_count = await db.emails.count_documents({
            "user_id": user["_id"],
            "folder": "trash"
        })
        
        return {
            "inbox": inbox_count,
            "purchases": purchases_count,
            "spam": spam_count,
            "trash": trash_count
        }
    except Exception as e:
        # Return zeros on error to avoid breaking the UI
        return {
            "inbox": 0,
            "purchases": 0,
            "spam": 0,
            "trash": 0
        }