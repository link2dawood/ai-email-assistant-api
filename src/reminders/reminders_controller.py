from fastapi import APIRouter, Depends
from src.auth.auth_service import auth_service
from src.prisma.database import get_db
from src.prisma.models import ReminderCreate
from datetime import datetime

router = APIRouter()

@router.get("/")
async def get_reminders(user = Depends(auth_service.get_current_user)):
    db = get_db()
    reminders = await db.reminders.find({"user_id": user["_id"]}).to_list(length=100)
    for r in reminders:
        r["id"] = str(r.pop("_id"))
    return reminders

@router.post("/")
async def create_reminder(req: ReminderCreate, user = Depends(auth_service.get_current_user)):
    db = get_db()
    data = req.dict()
    data["user_id"] = user["_id"]
    data["created_at"] = datetime.utcnow()
    data["is_completed"] = False
    res = await db.reminders.insert_one(data)
    return {"id": str(res.inserted_id), "message": "Reminder set"}