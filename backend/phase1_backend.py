import os
import sys
import subprocess

print("=" * 60)
print("  CyStar Backend - Phase 1: Auth + Crypto Engine")
print("=" * 60)
print()

if not os.path.exists("venv"):
    print("ERROR: Run this from the backend/ directory!")
    sys.exit(1)

def write_file(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  + {path}")

print("[1/3] Creating backend files...")
print()

# --- app/core/security.py ---
write_file('app/core/security.py', '''
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_EXPIRY_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> dict:
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    return {"user_id": user_id, "email": payload.get("email", "")}
''')

write_file('app/core/exceptions.py', '''
from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
''')

write_file('app/auth/schemas.py', '''
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
''')

write_file('app/auth/repository.py', '''
from app.core.database import users_collection


async def create_user(user_data: dict) -> dict:
    result = await users_collection.insert_one(user_data)
    user_data["_id"] = result.inserted_id
    return user_data


async def find_user_by_email(email: str):
    return await users_collection.find_one({"email": email})
''')

write_file('app/auth/service.py', '''
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
''')

write_file('app/auth/router.py', '''
from fastapi import APIRouter
from app.auth.schemas import RegisterRequest, LoginRequest, AuthResponse
from app.auth.service import register_user, login_user

router = APIRouter()


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    return await register_user(request.name, request.email, request.password)


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    return await login_user(request.email, request.password)
''')

write_file('app/credentials/crypto/utils.py', '''
import os
import json
import hashlib
import base64


def generate_salt(length: int = 16) -> str:
    return base64url_encode(os.urandom(length))


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def base64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def sha256_hash(data: str) -> str:
    digest = hashlib.sha256(data.encode("utf-8")).digest()
    return base64url_encode(digest)


def create_disclosure(salt: str, claim_name: str, claim_value: str) -> str:
    disclosure_array = [salt, claim_name, claim_value]
    disclosure_json = json.dumps(disclosure_array, separators=(",", ":"))
    return base64url_encode(disclosure_json.encode("utf-8"))


def hash_disclosure(disclosure: str) -> str:
    return sha256_hash(disclosure)


def decode_disclosure(disclosure: str) -> tuple:
    decoded_bytes = base64url_decode(disclosure)
    decoded_json = json.loads(decoded_bytes.decode("utf-8"))
    return tuple(decoded_json)
''')

write_file('app/credentials/crypto/ed25519.py', '''
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError


def generate_keypair() -> tuple:
    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key
    return (
        signing_key.encode().hex(),
        verify_key.encode().hex(),
    )


def sign(message: bytes, private_key_hex: str) -> str:
    signing_key = SigningKey(bytes.fromhex(private_key_hex))
    signed = signing_key.sign(message)
    return signed.signature.hex()


def verify(message: bytes, signature_hex: str, public_key_hex: str) -> bool:
    try:
        verify_key = VerifyKey(bytes.fromhex(public_key_hex))
        verify_key.verify(message, bytes.fromhex(signature_hex))
        return True
    except BadSignatureError:
        return False
''')

write_file('app/credentials/crypto/sd_jwt.py', '''
import json
import time
from app.credentials.crypto.utils import (
    generate_salt,
    base64url_encode,
    base64url_decode,
    create_disclosure,
    hash_disclosure,
    decode_disclosure,
)
from app.credentials.crypto import ed25519


def create_sd_jwt(
    claims: dict,
    issuer_name: str,
    subject: str,
    private_key_hex: str,
) -> dict:
    disclosures = {}
    sd_hashes = {}

    for claim_name, claim_value in claims.items():
        salt = generate_salt()
        disclosure = create_disclosure(salt, claim_name, str(claim_value))
        d_hash = hash_disclosure(disclosure)
        disclosures[claim_name] = disclosure
        sd_hashes[claim_name] = d_hash

    header = {"alg": "EdDSA", "typ": "sd-jwt"}

    payload = {
        "iss": issuer_name,
        "sub": subject,
        "iat": int(time.time()),
        "_sd": sorted(sd_hashes.values()),
        "_sd_alg": "sha-256",
    }

    header_b64 = base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}"

    signature = ed25519.sign(signing_input.encode("utf-8"), private_key_hex)
    signature_b64 = base64url_encode(bytes.fromhex(signature))

    sd_jwt = f"{signing_input}.{signature_b64}"

    return {
        "sd_jwt": sd_jwt,
        "disclosures": disclosures,
        "sd_hashes": sd_hashes,
    }


def create_presentation(
    sd_jwt: str,
    all_disclosures: dict,
    selected_fields: list,
) -> str:
    parts = [sd_jwt]
    for field in selected_fields:
        if field in all_disclosures:
            parts.append(all_disclosures[field])
    return "~".join(parts) + "~"


def verify_presentation(presentation: str, public_key_hex: str) -> dict:
    parts = presentation.rstrip("~").split("~")

    if len(parts) < 1:
        return {"verified": False, "error": "Invalid presentation format"}

    sd_jwt = parts[0]
    disclosure_strings = parts[1:]

    jwt_parts = sd_jwt.split(".")
    if len(jwt_parts) != 3:
        return {"verified": False, "error": "Invalid SD-JWT format"}

    header_b64, payload_b64, signature_b64 = jwt_parts

    signing_input = f"{header_b64}.{payload_b64}"
    signature_hex = base64url_decode(signature_b64).hex()

    if not ed25519.verify(signing_input.encode("utf-8"), signature_hex, public_key_hex):
        return {"verified": False, "error": "Signature verification failed"}

    payload = json.loads(base64url_decode(payload_b64).decode("utf-8"))
    sd_digests = set(payload.get("_sd", []))
    total_claims = len(sd_digests)

    disclosed_fields = {}
    matched_hashes = set()

    for disclosure in disclosure_strings:
        d_hash = hash_disclosure(disclosure)
        if d_hash not in sd_digests:
            return {"verified": False, "error": "Disclosure hash mismatch - data may be tampered"}

        salt, claim_name, claim_value = decode_disclosure(disclosure)
        disclosed_fields[claim_name] = claim_value
        matched_hashes.add(d_hash)

    return {
        "verified": True,
        "disclosed_fields": disclosed_fields,
        "issuer": payload.get("iss", ""),
        "subject": payload.get("sub", ""),
        "issued_at": payload.get("iat", 0),
        "total_claims": total_claims,
        "disclosed_count": len(disclosed_fields),
        "hidden_count": total_claims - len(disclosed_fields),
    }
''')

write_file('app/credentials/schemas.py', '''
from pydantic import BaseModel, Field
from typing import Optional


class IssueRequest(BaseModel):
    claims: dict = Field(..., min_length=1)
    issuer_name: str = Field(..., min_length=1)
    credential_title: str = Field(default="Credential", max_length=200)


class CredentialResponse(BaseModel):
    id: str
    credential_title: str
    issuer_name: str
    claims: dict
    created_at: str


class ShareRequest(BaseModel):
    credential_id: str
    selected_fields: list = Field(..., min_length=1)
    expires_in_hours: int = Field(default=24, ge=1, le=168)


class ShareResponse(BaseModel):
    share_token: str
    share_url: str
    expires_at: str
    selected_fields: list
''')

write_file('app/credentials/repository.py', '''
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
''')

write_file('app/credentials/service.py', '''
import uuid
from datetime import datetime, timedelta
from app.credentials.crypto import ed25519
from app.credentials.crypto.sd_jwt import create_sd_jwt, create_presentation
from app.credentials.repository import (
    save_credential,
    get_user_credentials,
    get_credential_by_id,
    save_presentation,
)
from app.core.exceptions import AppException
from app.core.config import get_settings

settings = get_settings()


async def issue_credential(user_id: str, claims: dict, issuer_name: str, credential_title: str) -> dict:
    private_key, public_key = ed25519.generate_keypair()

    sd_jwt_data = create_sd_jwt(
        claims=claims,
        issuer_name=issuer_name,
        subject=user_id,
        private_key_hex=private_key,
    )

    credential_data = {
        "user_id": user_id,
        "credential_title": credential_title,
        "issuer_name": issuer_name,
        "claims": claims,
        "sd_jwt": sd_jwt_data["sd_jwt"],
        "disclosures": sd_jwt_data["disclosures"],
        "sd_hashes": sd_jwt_data["sd_hashes"],
        "public_key": public_key,
        "private_key": private_key,
    }

    credential_id = await save_credential(credential_data)

    return {
        "id": credential_id,
        "credential_title": credential_title,
        "issuer_name": issuer_name,
        "claims": claims,
        "created_at": credential_data["created_at"].isoformat(),
    }


async def list_credentials(user_id: str) -> list:
    credentials = await get_user_credentials(user_id)
    return [
        {
            "id": c["_id"],
            "credential_title": c.get("credential_title", "Credential"),
            "issuer_name": c["issuer_name"],
            "claims": c["claims"],
            "created_at": c["created_at"].isoformat() if hasattr(c["created_at"], "isoformat") else str(c["created_at"]),
        }
        for c in credentials
    ]


async def share_credential(user_id: str, credential_id: str, selected_fields: list, expires_in_hours: int) -> dict:
    credential = await get_credential_by_id(credential_id, user_id)
    if not credential:
        raise AppException(status_code=404, detail="Credential not found")

    available_fields = list(credential["claims"].keys())
    invalid_fields = [f for f in selected_fields if f not in available_fields]
    if invalid_fields:
        raise AppException(
            status_code=400,
            detail=f"Invalid fields: {invalid_fields}. Available: {available_fields}",
        )

    presentation = create_presentation(
        sd_jwt=credential["sd_jwt"],
        all_disclosures=credential["disclosures"],
        selected_fields=selected_fields,
    )

    share_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

    presentation_data = {
        "share_token": share_token,
        "credential_id": credential_id,
        "user_id": user_id,
        "presentation": presentation,
        "public_key": credential["public_key"],
        "selected_fields": selected_fields,
        "total_fields": len(available_fields),
        "issuer_name": credential["issuer_name"],
        "credential_title": credential.get("credential_title", "Credential"),
        "expires_at": expires_at,
        "created_at": datetime.utcnow(),
    }

    await save_presentation(presentation_data)

    share_url = f"{settings.FRONTEND_URL}/verify/{share_token}"

    return {
        "share_token": share_token,
        "share_url": share_url,
        "expires_at": expires_at.isoformat(),
        "selected_fields": selected_fields,
    }
''')

write_file('app/credentials/router.py', '''
from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.credentials.schemas import IssueRequest, ShareRequest, ShareResponse
from app.credentials.service import issue_credential, list_credentials, share_credential

router = APIRouter()


@router.post("/issue")
async def issue(request: IssueRequest, user: dict = Depends(get_current_user)):
    return await issue_credential(
        user_id=user["user_id"],
        claims=request.claims,
        issuer_name=request.issuer_name,
        credential_title=request.credential_title,
    )


@router.get("/")
async def get_credentials(user: dict = Depends(get_current_user)):
    return await list_credentials(user["user_id"])


@router.post("/share", response_model=ShareResponse)
async def share(request: ShareRequest, user: dict = Depends(get_current_user)):
    return await share_credential(
        user_id=user["user_id"],
        credential_id=request.credential_id,
        selected_fields=request.selected_fields,
        expires_in_hours=request.expires_in_hours,
    )
''')

write_file('app/verification/schemas.py', '''
from pydantic import BaseModel
from typing import Optional


class VerificationResponse(BaseModel):
    verified: bool
    credential_title: Optional[str] = None
    disclosed_fields: Optional[dict] = None
    issuer: Optional[str] = None
    issued_at: Optional[int] = None
    total_claims: Optional[int] = None
    disclosed_count: Optional[int] = None
    hidden_count: Optional[int] = None
    expired: Optional[bool] = None
    error: Optional[str] = None
''')

write_file('app/verification/service.py', '''
from datetime import datetime
from app.credentials.repository import get_presentation_by_token
from app.credentials.crypto.sd_jwt import verify_presentation
from app.core.exceptions import AppException


async def verify_shared_credential(share_token: str) -> dict:
    presentation_doc = await get_presentation_by_token(share_token)
    if not presentation_doc:
        raise AppException(status_code=404, detail="Share link not found or expired")

    expired = False
    if "expires_at" in presentation_doc:
        expired = datetime.utcnow() > presentation_doc["expires_at"]

    if expired:
        return {
            "verified": False,
            "expired": True,
            "error": "This share link has expired",
        }

    result = verify_presentation(
        presentation=presentation_doc["presentation"],
        public_key_hex=presentation_doc["public_key"],
    )

    result["expired"] = expired
    result["credential_title"] = presentation_doc.get("credential_title", "Credential")

    return result
''')

write_file('app/verification/router.py', '''
from fastapi import APIRouter, Request
from app.verification.service import verify_shared_credential
from app.middleware.rate_limiter import limiter

router = APIRouter()


@router.get("/{share_token}")
@limiter.limit("10/minute")
async def verify(request: Request, share_token: str):
    return await verify_shared_credential(share_token)
''')

write_file('app/middleware/rate_limiter.py', '''
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
''')

write_file('app/main.py', '''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import get_settings
from app.core.database import create_indexes
from app.core.exceptions import AppException, app_exception_handler
from app.auth.router import router as auth_router
from app.credentials.router import router as credentials_router
from app.verification.router import router as verification_router
from app.middleware.rate_limiter import limiter

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_indexes()
    yield


app = FastAPI(
    title="CyStar Selective Disclosure API",
    description="IETF SD-JWT based selective disclosure and credential verification system",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Custom exception handler
app.add_exception_handler(AppException, app_exception_handler)

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


# Routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(credentials_router, prefix="/api/credentials", tags=["Credentials"])
app.include_router(verification_router, prefix="/api/verify", tags=["Verification"])
''')

write_file('tests/test_sd_jwt.py', '''
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.credentials.crypto.ed25519 import generate_keypair, sign, verify
from app.credentials.crypto.utils import (
    generate_salt,
    create_disclosure,
    hash_disclosure,
    decode_disclosure,
)
from app.credentials.crypto.sd_jwt import (
    create_sd_jwt,
    create_presentation,
    verify_presentation,
)


class TestEd25519:
    def test_generate_keypair(self):
        private_key, public_key = generate_keypair()
        assert len(private_key) == 64
        assert len(public_key) == 64

    def test_sign_and_verify(self):
        private_key, public_key = generate_keypair()
        message = b"hello world"
        signature = sign(message, private_key)
        assert verify(message, signature, public_key)

    def test_invalid_signature(self):
        private_key, public_key = generate_keypair()
        message = b"hello world"
        signature = sign(message, private_key)
        assert not verify(b"tampered message", signature, public_key)

    def test_wrong_key(self):
        private_key1, public_key1 = generate_keypair()
        _, public_key2 = generate_keypair()
        message = b"test"
        signature = sign(message, private_key1)
        assert not verify(message, signature, public_key2)


class TestDisclosures:
    def test_create_and_decode(self):
        salt = generate_salt()
        disclosure = create_disclosure(salt, "name", "Vishnu")
        decoded = decode_disclosure(disclosure)
        assert decoded == (salt, "name", "Vishnu")

    def test_hash_consistency(self):
        salt = generate_salt()
        d = create_disclosure(salt, "degree", "M.Sc")
        h1 = hash_disclosure(d)
        h2 = hash_disclosure(d)
        assert h1 == h2

    def test_different_salts(self):
        s1 = generate_salt()
        s2 = generate_salt()
        d1 = create_disclosure(s1, "name", "Vishnu")
        d2 = create_disclosure(s2, "name", "Vishnu")
        assert hash_disclosure(d1) != hash_disclosure(d2)


class TestSDJWT:
    def setup_method(self):
        self.private_key, self.public_key = generate_keypair()
        self.claims = {
            "name": "Vishnu Aravind",
            "degree": "M.Sc TCS",
            "college": "PSG College of Technology",
            "cgpa": "8.5",
            "graduationYear": "2028",
        }

    def test_create_sd_jwt(self):
        result = create_sd_jwt(self.claims, "PSG College", "user123", self.private_key)
        assert "sd_jwt" in result
        assert "disclosures" in result
        assert len(result["disclosures"]) == 5

    def test_full_disclosure(self):
        result = create_sd_jwt(self.claims, "PSG College", "user123", self.private_key)
        all_fields = list(self.claims.keys())
        presentation = create_presentation(result["sd_jwt"], result["disclosures"], all_fields)
        verification = verify_presentation(presentation, self.public_key)
        assert verification["verified"] is True
        assert len(verification["disclosed_fields"]) == 5
        assert verification["hidden_count"] == 0

    def test_selective_disclosure(self):
        result = create_sd_jwt(self.claims, "PSG College", "user123", self.private_key)
        selected = ["name", "degree"]
        presentation = create_presentation(result["sd_jwt"], result["disclosures"], selected)
        verification = verify_presentation(presentation, self.public_key)
        assert verification["verified"] is True
        assert len(verification["disclosed_fields"]) == 2
        assert "name" in verification["disclosed_fields"]
        assert "degree" in verification["disclosed_fields"]
        assert "cgpa" not in verification["disclosed_fields"]
        assert verification["hidden_count"] == 3

    def test_wrong_public_key(self):
        result = create_sd_jwt(self.claims, "PSG College", "user123", self.private_key)
        presentation = create_presentation(result["sd_jwt"], result["disclosures"], ["name"])
        _, wrong_key = generate_keypair()
        verification = verify_presentation(presentation, wrong_key)
        assert verification["verified"] is False

    def test_issuer_info_preserved(self):
        result = create_sd_jwt(self.claims, "PSG College", "user123", self.private_key)
        presentation = create_presentation(result["sd_jwt"], result["disclosures"], ["name"])
        verification = verify_presentation(presentation, self.public_key)
        assert verification["issuer"] == "PSG College"
        assert verification["subject"] == "user123"
''')


print()
print("[2/3] Running SD-JWT unit tests...")
print()

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/test_sd_jwt.py", "-v"],
    capture_output=True,
    text=True,
    cwd=os.getcwd(),
)
print(result.stdout)
if result.returncode != 0:
    print(result.stderr)

print()
print("[3/3] Syntax check...")
import py_compile
errors = []
for root, dirs, fnames in os.walk("app"):
    for fname in fnames:
        if fname.endswith(".py"):
            fpath = os.path.join(root, fname)
            try:
                py_compile.compile(fpath, doraise=True)
            except py_compile.PyCompileError as e:
                errors.append(str(e))
if errors:
    for e in errors:
        print(f"  ERROR: {e}")
else:
    print("  All files pass syntax check!")

print()
print("=" * 60)
print("  PHASE 1 COMPLETE!")
print("=" * 60)
print()
print("  Next steps:")
print("    1. Restart backend:")
print("       .\\venv\\Scripts\\python.exe -m uvicorn app.main:app --reload")
print("    2. Open http://localhost:8000/docs")
print("    3. Test: register -> issue -> share -> verify")
print()