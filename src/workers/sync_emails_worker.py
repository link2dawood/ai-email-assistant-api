import asyncio
from src.prisma.database import connect_db, disconnect_db, get_db
from src.gmail.gmail_service import gmail_service
from datetime import datetime
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SyncWorker")

async def sync_emails_job():
    """Iterates through active users and syncs their emails"""
    await connect_db()
    db = get_db()
    logger.info(f"[{datetime.utcnow()}] Starting Email Sync Job...")

    # Find users who have connected Gmail (pseudo-check)
    users = await db.users.find({}).to_list(length=100)
    
    for user in users:
        try:
            # Check if user has google tokens (simplified check)
            if "google_access_token" in user:
                logger.info(f"Syncing for user: {user['email']}")
                await gmail_service.fetch_emails(user)
        except Exception as e:
            logger.error(f"Error syncing {user.get('email')}: {e}")

    logger.info("Sync Job Completed.")
    await disconnect_db()

if __name__ == "__main__":
    asyncio.run(sync_emails_job())