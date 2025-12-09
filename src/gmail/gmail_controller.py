from fastapi import APIRouter, Depends
from src.auth.auth_service import auth_service
from src.gmail.gmail_service import gmail_service

router = APIRouter()

@router.post("/sync")
async def sync_gmail(current_user = Depends(auth_service.get_current_user)):
    result = await gmail_service.fetch_emails(current_user)
    return result