from pathlib import Path

code = r'''from fastapi import APIRouter
from fastapi.responses import JSONResponse
import traceback

from app.auth.schemas import RegisterRequest, LoginRequest
from app.auth.service import register_user, login_user

router = APIRouter()


@router.post("/register")
async def register(request: RegisterRequest):
    try:
        return await register_user(request.name, request.email, request.password)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.post("/login")
async def login(request: LoginRequest):
    try:
        return await login_user(request.email, request.password)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "traceback": traceback.format_exc(),
            },
        )
'''

Path("app/auth/router.py").write_text(code, encoding="utf-8")
print("auth/router.py patched")
