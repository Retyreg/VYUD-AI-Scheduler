from fastapi import APIRouter, HTTPException, Depends
from typing import List
import os
import sys
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import AccountCreate, AccountResponse, Platform
from services.auth import verify_token

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "")
BASE_URL = f"{SUPABASE_URL}/rest/v1/publisher_accounts"

def get_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

@router.get("/", response_model=List[AccountResponse])
async def get_accounts(user: dict = Depends(verify_token)):
    try:
        # Только аккаунты текущего пользователя
        url = f"{BASE_URL}?user_id=eq.{user['user_id']}"
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=AccountResponse)
async def connect_account(account: AccountCreate, user: dict = Depends(verify_token)):
    try:
        # Проверяем существующий аккаунт для этой платформы У ЭТОГО пользователя
        check_url = f"{BASE_URL}?platform=eq.{account.platform.value}&user_id=eq.{user['user_id']}"
        check_resp = requests.get(check_url, headers=get_headers())
        check_resp.raise_for_status()
        existing = check_resp.json()

        data = {
            "token": account.token,
            "channel_id": account.channel_id,
            "channel_name": account.channel_name,
            "is_active": True
        }

        if existing:
            # Обновляем существующий
            url = f"{BASE_URL}?id=eq.{existing[0]['id']}&user_id=eq.{user['user_id']}"
            response = requests.patch(url, json=data, headers=get_headers())
        else:
            # Создаём новый с user_id
            data["platform"] = account.platform.value
            data["user_id"] = user["user_id"]
            response = requests.post(BASE_URL, json=data, headers=get_headers())

        response.raise_for_status()
        return response.json()[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{account_id}")
async def disconnect_account(account_id: str, user: dict = Depends(verify_token)):
    try:
        # Отключаем только свой аккаунт
        url = f"{BASE_URL}?id=eq.{account_id}&user_id=eq.{user['user_id']}"
        data = {"is_active": False}
        response = requests.patch(url, json=data, headers=get_headers())
        response.raise_for_status()
        return {"disconnected": True, "id": account_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
