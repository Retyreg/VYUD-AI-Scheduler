from fastapi import APIRouter, HTTPException
from typing import List
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from models import AccountCreate, AccountResponse, Platform

router = APIRouter()

supabase = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_KEY", "")
)

@router.get("/", response_model=List[AccountResponse])
async def get_accounts():
    try:
        result = supabase.table("publisher_accounts").select("*").execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=AccountResponse)
async def connect_account(account: AccountCreate):
    try:
        existing = supabase.table("publisher_accounts")\
            .select("*")\
            .eq("platform", account.platform.value)\
            .execute()
        
        if existing.data:
            result = supabase.table("publisher_accounts")\
                .update({
                    "token": account.token,
                    "channel_id": account.channel_id,
                    "channel_name": account.channel_name,
                    "is_active": True
                })\
                .eq("id", existing.data[0]["id"])\
                .execute()
        else:
            result = supabase.table("publisher_accounts")\
                .insert({
                    "platform": account.platform.value,
                    "token": account.token,
                    "channel_id": account.channel_id,
                    "channel_name": account.channel_name,
                    "is_active": True
                })\
                .execute()
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{account_id}")
async def disconnect_account(account_id: str):
    try:
        supabase.table("publisher_accounts")\
            .update({"is_active": False})\
            .eq("id", account_id)\
            .execute()
        return {"disconnected": True, "id": account_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
