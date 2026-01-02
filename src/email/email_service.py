from src.prisma.database import get_db
from src.prisma.models import EmailCreate
from datetime import datetime

class EmailService:
    async def create_email(self, user_id, email_data: EmailCreate):
        data = email_data.dict()
        data["user_id"] = user_id
        data["created_at"] = datetime.utcnow()
        data["status"] = "sent"
        res = await get_db().emails.insert_one(data)
        return str(res.inserted_id)

    async def get_emails(self, user_id, limit=20):
        from bson import ObjectId
        
        # Ensure user_id is ObjectId for query
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        # Sort by _id desc (newest first)
        cursor = get_db().emails.find({"user_id": user_id}).sort("_id", -1).limit(limit)
        emails = await cursor.to_list(length=limit)
        
        # Convert ObjectId to str for response
        for email in emails:
            email["id"] = str(email.pop("_id"))
            if "user_id" in email:
                email["user_id"] = str(email["user_id"])
        return emails

email_service = EmailService()