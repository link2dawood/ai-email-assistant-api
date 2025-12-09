import asyncio
from src.prisma.database import connect_db, get_db, disconnect_db
from datetime import datetime

async def check_reminders():
    """Checks for reminders due now"""
    await connect_db()
    print("Worker: Checking reminders...")
    
    now = datetime.utcnow()
    db = get_db()
    
    # Logic to find due reminders
    # due = await db.reminders.find({"due_date": {"$lte": now}, "is_completed": False}).to_list(None)
    # for reminder in due:
    #     send_notification(reminder)
    
    print("Worker: Done.")
    await disconnect_db()

if __name__ == "__main__":
    asyncio.run(check_reminders())