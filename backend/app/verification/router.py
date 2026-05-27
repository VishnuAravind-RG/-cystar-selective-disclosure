
from fastapi import APIRouter, Request
from app.verification.service import verify_shared_credential
from app.middleware.rate_limiter import limiter

router = APIRouter()


@router.get("/{share_token}")
@limiter.limit("10/minute")
async def verify(request: Request, share_token: str):
    return await verify_shared_credential(share_token)
