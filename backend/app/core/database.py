from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings
import certifi

settings = get_settings()

client = AsyncIOMotorClient(
    settings.MONGODB_URL,
    tls=True,
    tlsAllowInvalidCertificates=True,
    tlsCAFile=certifi.where(),
)
db = client[settings.DATABASE_NAME]

users_collection = db['users']
credentials_collection = db['credentials']
presentations_collection = db['presentations']


async def create_indexes():
    await users_collection.create_index('email', unique=True)
    await credentials_collection.create_index('user_id')
    await presentations_collection.create_index('share_token', unique=True)
    await presentations_collection.create_index('expires_at', expireAfterSeconds=0)
