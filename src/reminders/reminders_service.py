from src.prisma.database import get_db
from src.prisma.models import ReminderCreate
from datetime import datetime
from bson import ObjectId

class RemindersService:
    async def create_reminder(self, user_id: str, reminder_data: ReminderCreate):
        db = get_db()
        data = reminder_data.dict()
        data["user_id"] = ObjectId(user_id)
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        data["is_completed"] = False
        
        result = await db.reminders.insert_one(data)
        return str(result.inserted_id)

    async def get_user_reminders(self, user_id: str, limit: int = 50):
        db = get_db()
        cursor = db.reminders.find({"user_id": ObjectId(user_id)}).sort("due_date", 1).limit(limit)
        reminders = await cursor.to_list(length=limit)
        
        # Format for API response
        for r in reminders:
            r["id"] = str(r.pop("_id"))
            r["user_id"] = str(r.pop("user_id"))
        return reminders

    async def mark_complete(self, reminder_id: str, user_id: str):
        db = get_db()
        result = await db.reminders.update_one(
            {"_id": ObjectId(reminder_id), "user_id": ObjectId(user_id)},
            {"$set": {"is_completed": True, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

reminders_service = RemindersService()