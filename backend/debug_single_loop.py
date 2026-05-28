import os, sys, asyncio, traceback, uuid
from datetime import datetime

if not os.path.exists("venv"):
    print("ERROR: Run from backend directory")
    sys.exit(1)

async def main():
    print("=" * 50)
    print("Single Loop Register Debug")
    print("=" * 50)

    try:
        print("[1] Importing modules")
        from app.core.security import hash_password, create_access_token
        from app.core.database import users_collection
        from app.auth.service import register_user

        print("[2] Password hashing")
        hashed = hash_password("test123")
        print("HASH OK:", hashed[:30])

        print("[3] MongoDB find")
        found = await users_collection.find_one({"email": "single_loop_check@test.com"})
        print("FIND OK:", found)

        print("[4] MongoDB direct insert")
        direct_email = f"direct_{uuid.uuid4().hex[:8]}@test.com"
        direct_user = {
            "name": "DirectUser",
            "email": direct_email,
            "password": hashed,
            "created_at": datetime.utcnow(),
        }
        insert_result = await users_collection.insert_one(direct_user)
        print("DIRECT INSERT OK:", insert_result.inserted_id)

        print("[5] JWT creation")
        token = create_access_token({"sub": str(insert_result.inserted_id), "email": direct_email})
        print("JWT OK:", token[:50])

        print("[6] Full register_user")
        service_email = f"service_{uuid.uuid4().hex[:8]}@test.com"
        result = await register_user("ServiceUser", service_email, "test123")
        print("REGISTER SERVICE OK:", result)

        print("=" * 50)
        print("ALL BACKEND AUTH STEPS WORKING")
        print("=" * 50)

    except Exception:
        traceback.print_exc()

asyncio.run(main())
