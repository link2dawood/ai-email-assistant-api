"""
=== FILE 1: app/routers/templates.py ===
Template Management Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId
import logging

from app import database
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

class TemplateCreate(BaseModel):
    name: str
    subject: str
    body: str
    is_default: bool = False

@router.get("/")
async def list_templates(current_user = Depends(get_current_user)):
    """List email templates"""
    templates = await database.templates_collection.find(
        {"user_id": current_user["_id"]}
    ).to_list(None)
    
    return {
        "templates": [
            {
                "id": str(t["_id"]),
                "name": t.get("name"),
                "subject": t.get("subject"),
                "body": t.get("body")[:100],
                "is_default": t.get("is_default", False)
            }
            for t in templates
        ]
    }

@router.post("/")
async def create_template(
    request: TemplateCreate,
    current_user = Depends(get_current_user)
):
    """Create new template"""
    template_data = {
        "user_id": current_user["_id"],
        "name": request.name,
        "subject": request.subject,
        "body": request.body,
        "is_default": request.is_default,
        "created_at": datetime.utcnow()
    }
    
    result = await database.templates_collection.insert_one(template_data)
    return {
        "message": "Template created",
        "template_id": str(result.inserted_id)
    }

@router.put("/{template_id}")
async def update_template(
    template_id: str,
    request: TemplateCreate,
    current_user = Depends(get_current_user)
):
    """Update template"""
    await database.templates_collection.update_one(
        {"_id": ObjectId(template_id), "user_id": current_user["_id"]},
        {"$set": request.dict()}
    )
    return {"message": "Template updated"}

@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user = Depends(get_current_user)
):
    """Delete template"""
    await database.templates_collection.delete_one({
        "_id": ObjectId(template_id),
        "user_id": current_user["_id"]
    })
    return {"message": "Template deleted"}


"""
=== FILE 2: app/routers/settings_router.py ===
User Settings Router
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime
import logging

from app import database
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

class SettingsUpdate(BaseModel):
    email_sync_enabled: bool = None
    email_sync_interval: int = None
    notifications_enabled: bool = None
    theme: str = None

@router.get("/")
async def get_settings(current_user = Depends(get_current_user)):
    """Get user settings"""
    settings = await database.user_settings_collection.find_one(
        {"user_id": current_user["_id"]}
    )
    
    if not settings:
        return {
            "email_sync_enabled": True,
            "email_sync_interval": 15,
            "notifications_enabled": True,
            "theme": "light"
        }
    
    return {
        "email_sync_enabled": settings.get("email_sync_enabled", True),
        "email_sync_interval": settings.get("email_sync_interval", 15),
        "notifications_enabled": settings.get("notifications_enabled", True),
        "theme": settings.get("theme", "light")
    }

@router.put("/")
async def update_settings(
    request: SettingsUpdate,
    current_user = Depends(get_current_user)
):
    """Update user settings"""
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await database.user_settings_collection.update_one(
        {"user_id": current_user["_id"]},
        {"$set": update_data},
        upsert=True
    )
    
    return {"message": "Settings updated", "settings": update_data}


"""
=== FILE 3: app/routers/admin.py ===
Admin Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
import logging

from app import database
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

async def verify_admin(current_user = Depends(get_current_user)):
    """Verify user is admin"""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@router.get("/stats")
async def get_stats(admin = Depends(verify_admin)):
    """Get system statistics"""
    total_users = await database.users_collection.count_documents({})
    total_emails = await database.emails_collection.count_documents({})
    
    return {
        "total_users": total_users,
        "total_emails": total_emails,
        "system_status": "healthy"
    }

@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 20,
    admin = Depends(verify_admin)
):
    """List all users (admin only)"""
    users = await database.users_collection.find(
        {}
    ).skip(skip).limit(limit).to_list(limit)
    
    return {
        "users": [
            {
                "id": str(u["_id"]),
                "email": u.get("email"),
                "name": u.get("name"),
                "created_at": u.get("created_at")
            }
            for u in users
        ]
    }

@router.get("/health")
async def system_health(admin = Depends(verify_admin)):
    """System health check"""
    return {
        "database": "connected",
        "status": "operational",
        "uptime": "running"
    }