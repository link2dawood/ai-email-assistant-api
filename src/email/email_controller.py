from fastapi import APIRouter, Depends
from src.auth.auth_service import auth_service
from src.email.email_service import email_service
from src.gmail.gmail_service import gmail_service
from src.prisma.models import EmailCreate

router = APIRouter()

# Support both with and without trailing slash
@router.get("/")
@router.get("")
async def list_emails(current_user = Depends(auth_service.get_current_user)):
    return await email_service.get_emails(current_user["_id"])

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