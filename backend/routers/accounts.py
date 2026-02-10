from fastapi import APIRouter, HTTPException
from typing import List
import os
import sys
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import AccountCreate, AccountResponse, Platform

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
BASE_URL = f"{SUPABASE_URL}/rest/v1/publisher_accounts"

def get_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

@router.get("/", response_model=List[AccountResponse])
async def get_accounts():
    try:
        response = requests.get(BASE_URL, headers=get_headers())
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=AccountResponse)
async def connect_account(account: AccountCreate):
    try:
        check_url = f"{BASE_URL}?platform=eq.{account.platform.value}"
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
            url = f"{BASE_URL}?id=eq.{existing[0]['id']}"
            response = requests.patch(url, json=data, headers=get_headers())
        else:
            data["platform"] = account.platform.value
            response = requests.post(BASE_URL, json=data, headers=get_headers())

        response.raise_for_status()
        return response.json()[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{account_id}")
async def disconnect_account(account_id: str):
    try:
        url = f"{BASE_URL}?id=eq.{account_id}"
        data = {"is_active": False}
        response = requests.patch(url, json=data, headers=get_headers())
        response.raise_for_status()
        return {"disconnected": True, "id": account_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
