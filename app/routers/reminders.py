from fastapi import APIRouter
router = APIRouter()

@router.get("/")
async def list_reminders():
    return {"message": "Reminders endpoint"}