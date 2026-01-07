from fastapi import APIRouter, Depends, HTTPException
from src.auth.auth_service import auth_service
from src.prisma.database import get_db
from bson import ObjectId
from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel

router = APIRouter()

class BulkActionRequest(BaseModel):
    email_ids: List[str]
    action: str  # 'archive', 'delete', 'mark-read', 'mark-unread'

class SnoozeRequest(BaseModel):
    until: str  # ISO datetime string

@router.post("/{email_id}/archive")
async def archive_email(email_id: str, current_user = Depends(auth_service.get_current_user)):
    """Move email to archive folder"""
    db = get_db()
    
    try:
        result = await db.emails.update_one(
            {"_id": ObjectId(email_id), "user_id": current_user["_id"]},
            {"$set": {"folder": "archive", "archived_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Email not found")
            
        return {"status": "success", "message": "Email archived"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{email_id}/delete")
async def delete_email(email_id: str, current_user = Depends(auth_service.get_current_user)):
    """Move email to trash"""
    db = get_db()
    
    try:
        result = await db.emails.update_one(
            {"_id": ObjectId(email_id), "user_id": current_user["_id"]},
            {"$set": {"folder": "trash", "deleted_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Email not found")
            
        return {"status": "success", "message": "Email moved to trash"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{email_id}/mark-read")
async def mark_email_read(email_id: str, current_user = Depends(auth_service.get_current_user)):
    """Mark email as read"""
    db = get_db()
    
    try:
        result = await db.emails.update_one(
            {"_id": ObjectId(email_id), "user_id": current_user["_id"]},
            {"$set": {"is_read": True, "read_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Email not found")
            
        return {"status": "success", "message": "Email marked as read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{email_id}/mark-unread")
async def mark_email_unread(email_id: str, current_user = Depends(auth_service.get_current_user)):
    """Mark email as unread"""
    db = get_db()
    
    try:
        result = await db.emails.update_one(
            {"_id": ObjectId(email_id), "user_id": current_user["_id"]},
            {"$set": {"is_read": False}, "$unset": {"read_at": ""}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Email not found")
            
        return {"status": "success", "message": "Email marked as unread"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{email_id}/snooze")
async def snooze_email(email_id: str, snooze_data: SnoozeRequest, current_user = Depends(auth_service.get_current_user)):
    """Snooze email until specified time"""
    db = get_db()
    
    try:
        # Parse the datetime string
        from dateutil import parser
        snooze_until = parser.parse(snooze_data.until)
        
        result = await db.emails.update_one(
            {"_id": ObjectId(email_id), "user_id": current_user["_id"]},
            {"$set": {
                "folder": "snoozed",
                "snoozed_until": snooze_until,
                "snoozed_at": datetime.utcnow()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Email not found")
            
        return {"status": "success", "message": f"Email snoozed until {snooze_until}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{email_id}/star")
async def star_email(email_id: str, current_user = Depends(auth_service.get_current_user)):
    """Star an email"""
    db = get_db()
    
    try:
        result = await db.emails.update_one(
            {"_id": ObjectId(email_id), "user_id": current_user["_id"]},
            {"$set": {"is_starred": True, "starred_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Email not found")
            
        return {"status": "success", "message": "Email starred"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{email_id}/unstar")
async def unstar_email(email_id: str, current_user = Depends(auth_service.get_current_user)):
    """Unstar an email"""
    db = get_db()
    
    try:
        result = await db.emails.update_one(
            {"_id": ObjectId(email_id), "user_id": current_user["_id"]},
            {"$set": {"is_starred": False}, "$unset": {"starred_at": ""}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Email not found")
            
        return {"status": "success", "message": "Email unstarred"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-action")
async def bulk_action(request: BulkActionRequest, current_user = Depends(auth_service.get_current_user)):
    """Perform bulk actions on multiple emails"""
    db = get_db()
    
    try:
        # Convert string IDs to ObjectIds
        object_ids = [ObjectId(eid) for eid in request.email_ids]
        
        update_data = {}
        if request.action == "archive":
            update_data = {"folder": "archive", "archived_at": datetime.utcnow()}
        elif request.action == "delete":
            update_data = {"folder": "trash", "deleted_at": datetime.utcnow()}
        elif request.action == "mark-read":
            update_data = {"is_read": True, "read_at": datetime.utcnow()}
        elif request.action == "mark-unread":
            update_data = {"is_read": False}
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        result = await db.emails.update_many(
            {"_id": {"$in": object_ids}, "user_id": current_user["_id"]},
            {"$set": update_data}
        )
        
        return {
            "status": "success",
            "message": f"Bulk {request.action} completed",
            "modified_count": result.modified_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
