import logging
from motor.motor_asyncio import AsyncIOMotorClient
from src.config import settings
import ssl
import certifi

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

    async def connect_db(self):
        try:
            logger.info(f"Connecting to MongoDB: {settings.mongodb_uri}")
            
            # Create SSL context that doesn't verify certificates
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Connect
            self.client = AsyncIOMotorClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000,
                tlsAllowInvalidCertificates=True,
            )
            
            # Verify connection
            await self.client.admin.command('ping')
            logger.info("✓ MongoDB connected successfully")
            
            # Get database
            self.db = self.client[settings.database_name]
            logger.info(f"✓ Database '{settings.database_name}' selected")
            
        except Exception as e:
            logger.error(f"✗ MongoDB connection failed: {str(e)}")
            raise

    async def disconnect_db(self):
        if self.client:
            self.client.close()
            logger.info("✓ MongoDB disconnected")

    async def create_indexes(self):
        # ... (keep your index creation logic here) ...
        pass

# Create global database instance
db_instance = Database()

def get_db():
    return db_instance.db

async def connect_db():
    await db_instance.connect_db()

async def disconnect_db():
    await db_instance.disconnect_db()