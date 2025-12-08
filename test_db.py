import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import certifi

async def test_connection():
    print(f"Testing connection to: {settings.mongodb_url.split('@')[1] if '@' in settings.mongodb_url else '...'}...")
    try:
        client = AsyncIOMotorClient(settings.mongodb_url)
        await client.admin.command('ping')
        print("✅ Success!")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
