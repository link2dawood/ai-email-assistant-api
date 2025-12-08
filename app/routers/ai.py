from fastapi import APIRouter, HTTPException, Depends
from app.models import EmailClassifyRequest, EmailClassifyResponse, EmailReplyRequest, EmailReplyResponse
from app.services.openai_service import analyze_email, generate_reply
from app.utils.auth import get_current_user

router = APIRouter()

@router.post("/classify", response_model=EmailClassifyResponse)
async def classify_email(
    request: EmailClassifyRequest,
    current_user = Depends(get_current_user)
):
    """Classify an email using AI"""
    try:
        result = analyze_email(request.email_content)
        return EmailClassifyResponse(
            category=result.get("category", "Uncategorized"),
            confidence=float(result.get("importance", 0)) / 100.0, # Normalize to 0-1
            summary=result.get("summary", ""),
            sentiment=result.get("sentiment", "Neutral")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reply", response_model=EmailReplyResponse)
async def reply_email(
    request: EmailReplyRequest,
    current_user = Depends(get_current_user)
):
    """Generate a reply for an email"""
    try:
        reply = generate_reply(request.email_content, request.tone)
        return EmailReplyResponse(
            reply_text=reply,
            confidence=0.9 # Placeholder confidence
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))