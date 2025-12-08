"""
MongoDB Database Connection Module
Handles all database initialization and collections
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from contextlib import asynccontextmanager
from app.config import settings

logger = logging.getLogger(__name__)

# Global database client and instance
client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None

# ============ Collection References ============
users_collection: AsyncIOMotorCollection = None
emails_collection: AsyncIOMotorCollection = None
drafts_collection: AsyncIOMotorCollection = None
templates_collection: AsyncIOMotorCollection = None
scheduled_emails_collection: AsyncIOMotorCollection = None
email_sync_logs_collection: AsyncIOMotorCollection = None
api_keys_collection: AsyncIOMotorCollection = None
subscriptions_collection: AsyncIOMotorCollection = None
user_settings_collection: AsyncIOMotorCollection = None


async def connect_db():
    """
    Connect to MongoDB and initialize collections
    """
    global client, db
    global users_collection, emails_collection, drafts_collection
    global templates_collection, scheduled_emails_collection
    global email_sync_logs_collection, api_keys_collection
    global subscriptions_collection, user_settings_collection
    
    try:
        logger.info(f"Connecting to MongoDB: {settings.mongodb_uri}")
        
        # Create async MongoDB client
        client = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            retryWrites=True
        )
        
        # Verify connection
        await client.admin.command('ping')
        logger.info("✓ MongoDB connection successful")
        
        # Get database instance
        db = client[settings.database_name]
        
        # Initialize collections
        users_collection = db["users"]
        emails_collection = db["emails"]
        drafts_collection = db["drafts"]
        templates_collection = db["templates"]
        scheduled_emails_collection = db["scheduled_emails"]
        email_sync_logs_collection = db["email_sync_logs"]
        api_keys_collection = db["api_keys"]
        subscriptions_collection = db["subscriptions"]
        user_settings_collection = db["user_settings"]
        
        # Create indexes
        await create_indexes()
        
        logger.info("✓ All collections initialized")
        
    except Exception as e:
        logger.error(f"✗ MongoDB connection failed: {str(e)}")
        raise


async def disconnect_db():
    """
    Disconnect from MongoDB
    """
    global client
    
    if client is not None:
        client.close()
        logger.info("✓ MongoDB disconnected")


async def create_indexes():
    """
    Create database indexes for optimal query performance
    """
    try:
        # Users collection indexes
        await users_collection.create_index("email", unique=True)
        await users_collection.create_index("created_at")
        await users_collection.create_index("subscription_plan")
        
        # Emails collection indexes
        await emails_collection.create_index("user_id")
        await emails_collection.create_index([("user_id", 1), ("gmail_id", 1)], unique=True)
        await emails_collection.create_index("received_at")
        await emails_collection.create_index("is_read")
        await emails_collection.create_index([("user_id", 1), ("labels", 1)])
        await emails_collection.create_index([("user_id", 1), ("created_at", -1)])
        
        # Drafts collection indexes
        await drafts_collection.create_index("user_id")
        await drafts_collection.create_index([("user_id", 1), ("created_at", -1)])
        
        # Templates collection indexes
        await templates_collection.create_index("user_id")
        await templates_collection.create_index([("user_id", 1), ("is_default", 1)])
        
        # Scheduled emails indexes
        await scheduled_emails_collection.create_index("user_id")
        await scheduled_emails_collection.create_index("scheduled_time")
        await scheduled_emails_collection.create_index([("user_id", 1), ("status", 1)])
        
        # Email sync logs indexes
        await email_sync_logs_collection.create_index("user_id")
        await email_sync_logs_collection.create_index("sync_timestamp")
        await email_sync_logs_collection.create_index([("user_id", 1), ("status", 1)])
        
        # API Keys indexes
        await api_keys_collection.create_index("user_id")
        await api_keys_collection.create_index("key", unique=True)
        
        # Subscriptions indexes
        await subscriptions_collection.create_index("user_id", unique=True)
        await subscriptions_collection.create_index("stripe_customer_id")
        await subscriptions_collection.create_index("stripe_subscription_id")
        
        # User settings indexes
        await user_settings_collection.create_index("user_id", unique=True)
        
        logger.info("✓ All indexes created successfully")
        
    except Exception as e:
        logger.error(f"✗ Index creation failed: {str(e)}")
        # Don't raise - indexes might already exist


def get_database() -> AsyncIOMotorDatabase:
    """
    Get database instance for use in routes
    """
    if db is None:
        raise RuntimeError("Database not initialized. Call connect_db() first.")
    return db


@asynccontextmanager
async def get_db_session():
    """
    Context manager for database sessions
    Usage:
        async with get_db_session() as session:
            # Use session for operations
    """
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        pass