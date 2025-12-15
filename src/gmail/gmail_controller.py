from fastapi import APIRouter, Depends
from src.auth.auth_service import auth_service
from src.gmail.gmail_service import gmail_service

router = APIRouter()

@router.post("/sync")
async def sync_gmail(current_user = Depends(auth_service.get_current_user)):
    result = await gmail_service.fetch_emails(current_user)
    return result

@router.get("/stats")
async def get_stats(user = Depends(auth_service.get_current_user)):
    """
    Return statistics for the sidebar.
    For MVP/Mock, we return 0s to avoid hardcoded fake numbers.
    In future, this should fetch real counts from Gmail API.
    """
    return {
        "inbox": 0,
        "purchases": 0,
        "spam": 0,
        "trash": 0
    }