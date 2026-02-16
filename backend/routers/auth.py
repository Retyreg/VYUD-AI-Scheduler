from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.auth import signup, login, refresh_token, logout, verify_token

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    access_token: str

@router.post("/register")
async def register(request: RegisterRequest):
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    result = await signup(request.email, request.password)
    return {"message": "Registration successful. Check email to confirm.", "user_id": result.get("user", {}).get("id"), "email": request.email}

@router.post("/login")
async def login_user(request: LoginRequest):
    return await login(request.email, request.password)

@router.post("/refresh")
async def refresh_access_token(request: RefreshRequest):
    return await refresh_token(request.refresh_token)

@router.post("/logout")
async def logout_user(request: LogoutRequest):
    success = await logout(request.access_token)
    return {"success": success}

@router.get("/me")
async def get_current_user(user: dict = Depends(verify_token)):
    return {"id": user["user_id"], "email": user["email"], "role": user["role"]}

@router.get("/check")
async def check_auth(user: dict = Depends(verify_token)):
    return {"authenticated": True, "user_id": user["user_id"]}
