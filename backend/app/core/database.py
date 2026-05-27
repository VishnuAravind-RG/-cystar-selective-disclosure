from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings

settings = get_settings()

client = AsyncIOMotorClient(settings.MONGODB_URL)
db = client[settings.DATABASE_NAME]

# Collections
users_collection = db["users"]
credentials_collection = db["credentials"]
presentations_collection = db["presentations"]


async def create_indexes():
    """Create database indexes on startup."""
    await users_collection.create_index("email", unique=True)
    await credentials_collection.create_index("user_id")
    await presentations_collection.create_index("share_token", unique=True)
    await presentations_collection.create_index(
        "expires_at", expireAfterSeconds=0
    )  # TTL index — auto-deletes expired presentations
