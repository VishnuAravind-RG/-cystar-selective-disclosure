import os, sys, asyncio, traceback, uuid

if not os.path.exists("venv"):
    print("ERROR: Run from backend directory")
    sys.exit(1)

print("=" * 50)
print("Debug Register")
print("=" * 50)

print("[1] Password hashing")
try:
    from app.core.security import hash_password, create_access_token
    hashed = hash_password("test123")
    print("HASH OK:", hashed[:30])
except Exception:
    traceback.print_exc()
    sys.exit(1)

print("[2] MongoDB find")
try:
    from app.core.database import users_collection

    async def test_find():
        return await users_collection.find_one({"email": "debug_check@test.com"})

    found = asyncio.run(test_find())
    print("FIND OK:", found)
except Exception:
    traceback.print_exc()
    sys.exit(1)

print("[3] Full register_user")
try:
    from app.auth.service import register_user

    async def test_register():
        email = f"debug_{uuid.uuid4().hex[:8]}@test.com"
        print("EMAIL:", email)
        return await register_user("DebugUser", email, "test123")

    result = asyncio.run(test_register())
    print("REGISTER OK:", result)
except Exception:
    traceback.print_exc()

print("=" * 50)
print("Done")
print("=" * 50)
