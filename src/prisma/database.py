import logging
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager

# ---------------------------------------------------------
# FIX: Change 'app.config' to 'src.config'
# ---------------------------------------------------------
from src.config import settings 

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

    async def connect_db(self):
        try:
            logger.info(f"Connecting to MongoDB: {settings.mongodb_uri}")
            self.client = AsyncIOMotorClient(settings.mongodb_uri)
            # Verify connection
            await self.client.admin.command('ping')
            self.db = self.client[settings.database_name]
            print("✓ MongoDB connected")
        except Exception as e:
            logger.error(f"✗ MongoDB connection failed: {str(e)}")
            raise

    async def disconnect_db(self):
        if self.client:
            self.client.close()
            print("✓ MongoDB disconnected")

# Create a global instance
db_instance = Database()

def get_db():
    """Helper to get the database instance in other files"""
    return db_instance.db

async def connect_db():
    await db_instance.connect_db()

async def disconnect_db():
    await db_instance.disconnect_db()