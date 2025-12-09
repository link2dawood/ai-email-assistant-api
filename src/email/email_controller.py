from fastapi import APIRouter, Depends
from src.auth.auth_service import auth_service
from src.email.email_service import email_service
from src.prisma.models import EmailCreate

router = APIRouter()

@router.get("/")
async def list_emails(current_user = Depends(auth_service.get_current_user)):
    return await email_service.get_emails(current_user["_id"])

@router.post("/send")
async def send_email(
    email: EmailCreate, 
    current_user = Depends(auth_service.get_current_user)
):
    email_id = await email_service.create_email(current_user["_id"], email)
    return {"message": "Email sent", "id": email_id}