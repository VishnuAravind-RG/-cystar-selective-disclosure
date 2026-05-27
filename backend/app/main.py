
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
