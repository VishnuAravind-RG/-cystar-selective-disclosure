
from app.core.database import users_collection


async def create_user(user_data: dict) -> dict:
    result = await users_collection.insert_one(user_data)
    user_data["_id"] = result.inserted_id
    return user_data


async def find_user_by_email(email: str):
    return await users_collection.find_one({"email": email})
