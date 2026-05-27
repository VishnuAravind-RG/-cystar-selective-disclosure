
from app.auth.repository import create_user, find_user_by_email
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import AppException
from datetime import datetime


async def register_user(name: str, email: str, password: str) -> dict:
    existing = await find_user_by_email(email)
    if existing:
        raise AppException(status_code=409, detail="Email already registered")

    user_data = {
        "name": name,
        "email": email,
        "password": hash_password(password),
        "created_at": datetime.utcnow(),
    }

    user = await create_user(user_data)
    user_id = str(user["_id"])

    token = create_access_token({"sub": user_id, "email": email})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user_id, "email": email, "name": name},
    }


async def login_user(email: str, password: str) -> dict:
    user = await find_user_by_email(email)
    if not user:
        raise AppException(status_code=401, detail="Invalid email or password")

    if not verify_password(password, user["password"]):
        raise AppException(status_code=401, detail="Invalid email or password")

    user_id = str(user["_id"])
    token = create_access_token({"sub": user_id, "email": email})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user_id, "email": email, "name": user["name"]},
    }
