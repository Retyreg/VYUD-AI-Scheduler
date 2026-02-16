"""
Supabase Auth Service
"""
import os
import requests
from fastapi import HTTPException, Header
from typing import Optional
import jwt

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
AUTH_URL = f"{SUPABASE_URL}/auth/v1"

def get_auth_headers():
    return {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}

async def signup(email: str, password: str) -> dict:
    response = requests.post(f"{AUTH_URL}/signup", headers=get_auth_headers(), json={"email": email, "password": password})
    data = response.json()
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=data.get("error_description") or data.get("msg") or "Registration failed")
    return data

async def login(email: str, password: str) -> dict:
    response = requests.post(f"{AUTH_URL}/token?grant_type=password", headers=get_auth_headers(), json={"email": email, "password": password})
    data = response.json()
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail=data.get("error_description") or "Invalid credentials")
    return {"access_token": data["access_token"], "refresh_token": data["refresh_token"], "expires_in": data["expires_in"], "user": {"id": data["user"]["id"], "email": data["user"]["email"]}}

async def refresh_token(ref_token: str) -> dict:
    response = requests.post(f"{AUTH_URL}/token?grant_type=refresh_token", headers=get_auth_headers(), json={"refresh_token": ref_token})
    data = response.json()
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return {"access_token": data["access_token"], "refresh_token": data["refresh_token"], "expires_in": data["expires_in"]}

async def logout(access_token: str) -> bool:
    headers = get_auth_headers()
    headers["Authorization"] = f"Bearer {access_token}"
    response = requests.post(f"{AUTH_URL}/logout", headers=headers)
    return response.status_code == 204

def verify_token(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        if SUPABASE_JWT_SECRET:
            payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
        else:
            headers = get_auth_headers()
            headers["Authorization"] = f"Bearer {token}"
            response = requests.get(f"{AUTH_URL}/user", headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
            payload = response.json()
        return {"user_id": payload.get("sub") or payload.get("id"), "email": payload.get("email"), "role": payload.get("role", "authenticated")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
