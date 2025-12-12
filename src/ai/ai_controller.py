from fastapi import APIRouter, Depends
from src.auth.auth_service import auth_service
from src.ai.ai_service import ai_service
from src.prisma.models import AIRequest

# Define the router variable here
router = APIRouter()

@router.post("/classify")
async def classify(req: AIRequest, user = Depends(auth_service.get_current_user)):
    return await ai_service.analyze_text(req.text)

@router.post("/reply")
async def generate_reply(req: AIRequest, user = Depends(auth_service.get_current_user)):
    try:
        reply = await ai_service.generate_reply(req.text, req.tone)
        return {"reply": reply}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))