import os
import sys
import socket
import subprocess
import importlib
from pathlib import Path

print("=" * 70)
print("CyStar Backend Verification Script")
print("=" * 70)

ROOT = Path.cwd()
print(f"Current directory: {ROOT}")

checks = []

def ok(name, detail=""):
    checks.append((name, True, detail))
    print(f"[OK] {name} {detail}")

def fail(name, detail=""):
    checks.append((name, False, detail))
    print(f"[FAIL] {name} {detail}")

# 1. Directory check
if (ROOT / "venv").exists() and (ROOT / "app").exists():
    ok("Running from backend directory")
else:
    fail("Run location", "Run this from cystar-selective-disclosure/backend")

# 2. Important files
required_files = [
    "app/main.py",
    "app/core/config.py",
    "app/core/database.py",
    "app/core/security.py",
    "app/auth/router.py",
    "app/auth/service.py",
    "app/auth/repository.py",
    "app/auth/schemas.py",
    "app/credentials/crypto/sd_jwt.py",
    "app/credentials/crypto/ed25519.py",
    "app/credentials/crypto/utils.py",
    ".env",
]
for f in required_files:
    p = ROOT / f
    if p.exists() and p.stat().st_size > 0:
        ok(f"File exists: {f}")
    else:
        fail(f"Missing/empty file: {f}")

# 3. Env sanity
try:
    env_text = (ROOT / ".env").read_text(encoding="utf-8")
    if "&amp;" in env_text:
        fail(".env encoding", "Found &amp; in MongoDB URL. Replace with &")
    else:
        ok(".env encoding", "No &amp; found")
    if "MONGODB_URL=" in env_text and "JWT_SECRET=" in env_text:
        ok(".env required keys")
    else:
        fail(".env required keys", "Missing MONGODB_URL or JWT_SECRET")
except Exception as e:
    fail(".env read", str(e))

# 4. Python imports
imports = [
    "fastapi",
    "uvicorn",
    "motor",
    "pymongo",
    "jose",
    "passlib",
    "nacl",
    "slowapi",
    "certifi",
    "httpx",
]
for mod in imports:
    try:
        importlib.import_module(mod)
        ok(f"Import: {mod}")
    except Exception as e:
        fail(f"Import: {mod}", str(e))

# 5. App imports
try:
    from app.main import app
    routes = sorted([r.path for r in app.routes])
    ok("FastAPI app import")
    expected_routes = ["/health", "/api/auth/register", "/api/auth/login", "/api/credentials/issue", "/api/credentials/", "/api/credentials/share", "/api/verify/{share_token}"]
    for route in expected_routes:
        if route in routes:
            ok(f"Route exists: {route}")
        else:
            fail(f"Route missing: {route}")
except Exception as e:
    fail("FastAPI app import", repr(e))

# 6. Auth logic direct test
try:
    import asyncio, uuid
    from app.auth.service import register_user

    async def direct_register():
        email = f"verify_{uuid.uuid4().hex[:8]}@test.com"
        result = await register_user("VerifyUser", email, "test123")
        return result

    result = asyncio.run(direct_register())
    if result.get("access_token") and result.get("user"):
        ok("Direct register_user service", f"Created {result['user']['email']}")
    else:
        fail("Direct register_user service", "No token/user returned")
except Exception as e:
    fail("Direct register_user service", repr(e))

# 7. Port 8000 check
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1)
try:
    result = s.connect_ex(("127.0.0.1", 8000))
    if result == 0:
        ok("Port 8000", "Something is listening on 127.0.0.1:8000")
    else:
        ok("Port 8000", "Free right now")
finally:
    s.close()

# 8. PowerShell process info helper
print("\nPowerShell command to inspect port 8000:")
print("Get-NetTCPConnection -LocalPort 8000 -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess")

print("\n" + "=" * 70)
passed = sum(1 for _, status, _ in checks if status)
failed = sum(1 for _, status, _ in checks if not status)
print(f"Summary: {passed} passed, {failed} failed")
if failed == 0:
    print("READY: Backend files, imports, routes, env, and direct auth logic look good.")
    print("Next safe start command:")
    print(r".\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
else:
    print("NOT READY: Fix the failed checks above before starting.")
print("=" * 70)
