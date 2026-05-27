
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
