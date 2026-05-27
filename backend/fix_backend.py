import os
import sys

print("=" * 50)
print("  CyStar Backend — File Fix Script")
print("=" * 50)
print()

# Make sure we're in the backend directory
if not os.path.exists("venv"):
    print("ERROR: Run this from the backend/ directory!")
    print("  cd cystar-selective-disclosure\\backend")
    print("  python fix_backend.py")
    sys.exit(1)

# ============================================================
# 1. Content files
# ============================================================

MAIN_PY = """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.core.database import create_indexes

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    \"\"\"Startup and shutdown events.\"\"\"
    await create_indexes()
    yield


app = FastAPI(
    title="CyStar Selective Disclosure API",
    description="IETF SD-JWT based selective disclosure and credential verification system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cystar-sd-api"}


# Routers will be added here as we build them
# from app.auth.router import router as auth_router
# from app.credentials.router import router as credentials_router
# from app.verification.router import router as verification_router
# app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(credentials_router, prefix="/api/credentials", tags=["Credentials"])
# app.include_router(verification_router, prefix="/api/verify", tags=["Verification"])
"""

CONFIG_PY = """from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # MongoDB
    MONGODB_URL: str
    DATABASE_NAME: str = "cystar"

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
"""

DATABASE_PY = """from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings

settings = get_settings()

client = AsyncIOMotorClient(settings.MONGODB_URL)
db = client[settings.DATABASE_NAME]

# Collections
users_collection = db["users"]
credentials_collection = db["credentials"]
presentations_collection = db["presentations"]


async def create_indexes():
    \"\"\"Create database indexes on startup.\"\"\"
    await users_collection.create_index("email", unique=True)
    await credentials_collection.create_index("user_id")
    await presentations_collection.create_index("share_token", unique=True)
    await presentations_collection.create_index(
        "expires_at", expireAfterSeconds=0
    )  # TTL index — auto-deletes expired presentations
"""

DOCKERFILE = """FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

ENV_EXAMPLE = """# MongoDB Atlas connection string
MONGODB_URL=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority

# Database name
DATABASE_NAME=cystar

# JWT Configuration
JWT_SECRET=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=60

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000
"""

REQUIREMENTS = """fastapi==0.115.0
uvicorn[standard]==0.30.0
motor==3.5.0
pymongo==4.8.0
pydantic[email]==2.8.0
pydantic-settings==2.4.0
python-jose[cryptography]==3.3.0
PyNaCl==1.5.0
passlib[bcrypt]==1.7.4
slowapi==0.1.9
python-multipart==0.0.9
httpx==0.27.0
pytest==8.3.0
pytest-asyncio==0.23.0
"""

# ============================================================
# 2. File mapping
# ============================================================

content_files = {
    "app/main.py": MAIN_PY,
    "app/core/config.py": CONFIG_PY,
    "app/core/database.py": DATABASE_PY,
    "Dockerfile": DOCKERFILE,
    ".env.example": ENV_EXAMPLE,
    "requirements.txt": REQUIREMENTS,
}

# Empty files (placeholders + __init__.py)
empty_files = [
    "app/__init__.py",
    "app/core/__init__.py",
    "app/auth/__init__.py",
    "app/credentials/__init__.py",
    "app/credentials/crypto/__init__.py",
    "app/verification/__init__.py",
    "app/middleware/__init__.py",
    "tests/__init__.py",
    "app/auth/router.py",
    "app/auth/service.py",
    "app/auth/repository.py",
    "app/auth/schemas.py",
    "app/credentials/router.py",
    "app/credentials/service.py",
    "app/credentials/repository.py",
    "app/credentials/schemas.py",
    "app/credentials/crypto/sd_jwt.py",
    "app/credentials/crypto/ed25519.py",
    "app/credentials/crypto/utils.py",
    "app/verification/router.py",
    "app/verification/service.py",
    "app/verification/schemas.py",
    "app/middleware/rate_limiter.py",
    "app/middleware/logging_config.py",
    "app/core/security.py",
    "app/core/exceptions.py",
    "tests/test_auth.py",
    "tests/test_credentials.py",
    "tests/test_sd_jwt.py",
]

# ============================================================
# 3. Create files
# ============================================================

print("[1/3] Creating content files...")
for path, content in content_files.items():
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  + {path} ({len(content)} bytes)")

print()
print("[2/3] Creating placeholder files...")
for path in empty_files:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("")
        print(f"  + {path}")
    else:
        print(f"  ~ {path} (already exists)")

# Copy .env.example to .env if .env doesn't exist
if not os.path.exists(".env"):
    with open(".env", "w", encoding="utf-8") as f:
        f.write(ENV_EXAMPLE)
    print("  + .env (copied from .env.example)")

print()
print("[3/3] Verifying import...")

# Test the import
try:
    # We need to add current dir to path
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())

    # Can't actually import because it needs MongoDB running,
    # but we can check the files exist and have content
    assert os.path.exists("app/main.py"), "app/main.py missing"
    assert os.path.exists("app/core/config.py"), "app/core/config.py missing"
    assert os.path.exists("app/core/database.py"), "app/core/database.py missing"
    assert os.path.exists("app/__init__.py"), "app/__init__.py missing"
    assert os.path.exists("app/core/__init__.py"), "app/core/__init__.py missing"
    assert os.path.getsize("app/main.py") > 100, "app/main.py is empty"
    assert os.path.getsize("app/core/config.py") > 100, "app/core/config.py is empty"
    assert os.path.getsize("app/core/database.py") > 100, "app/core/database.py is empty"
    print("  All files verified!")
except AssertionError as e:
    print(f"  FAILED: {e}")

print()
print("=" * 50)
print("  DONE!")
print("=" * 50)
print()
print("  Next: Edit .env with your MongoDB URL:")
print("    MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/...")
print("    JWT_SECRET=any-random-string-here")
print()
print("  Then test:")
print("    .\\venv\\Scripts\\activate")
print("    uvicorn app.main:app --reload")
print("    Open http://localhost:8000/health")
print()
