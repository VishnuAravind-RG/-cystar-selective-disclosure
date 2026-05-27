
from datetime import datetime
from bson import ObjectId
from app.core.database import credentials_collection, presentations_collection


async def save_credential(credential_data: dict) -> str:
    credential_data["created_at"] = datetime.utcnow()
    result = await credentials_collection.insert_one(credential_data)
    return str(result.inserted_id)


async def get_user_credentials(user_id: str) -> list:
    cursor = credentials_collection.find({"user_id": user_id}).sort("created_at", -1)
    credentials = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        credentials.append(doc)
    return credentials


async def get_credential_by_id(credential_id: str, user_id: str):
    try:
        doc = await credentials_collection.find_one({
            "_id": ObjectId(credential_id),
            "user_id": user_id,
        })
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc
    except Exception:
        return None


async def save_presentation(presentation_data: dict) -> str:
    result = await presentations_collection.insert_one(presentation_data)
    return str(result.inserted_id)


async def get_presentation_by_token(share_token: str):
    return await presentations_collection.find_one({"share_token": share_token})
