from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import re
import requests

router = APIRouter()

# Supabase REST API через HTTP
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
BASE_URL = f"{SUPABASE_URL}/rest/v1/prompts"

def get_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }


class PromptCreate(BaseModel):
    name: str
    type: str = "post"
    platform: Optional[str] = None
    content: str
    is_default: bool = False

class PromptUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    platform: Optional[str] = None
    content: Optional[str] = None
    is_default: Optional[bool] = None

class PromptResponse(BaseModel):
    id: str
    name: str
    type: str
    platform: Optional[str]
    content: str
    is_default: bool
    created_at: datetime
    updated_at: datetime
    variables: List[str] = []


def extract_variables(content: str) -> List[str]:
    return list(set(re.findall(r'\{\{(\w+)\}\}', content)))

def enrich_prompt(data: dict) -> dict:
    data["variables"] = extract_variables(data.get("content", ""))
    return data


@router.get("/", response_model=List[PromptResponse])
async def get_prompts(type: Optional[str] = None, platform: Optional[str] = None):
    try:
        url = BASE_URL + "?order=created_at.asc"
        if type:
            url += f"&type=eq.{type}"
        if platform:
            url += f"&or=(platform.eq.{platform},platform.is.null)"
        
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        data = response.json()
        return [enrich_prompt(p) for p in data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=PromptResponse)
async def create_prompt(prompt: PromptCreate):
    try:
        data = {
            "name": prompt.name,
            "type": prompt.type,
            "platform": prompt.platform,
            "content": prompt.content,
            "is_default": prompt.is_default,
        }
        response = requests.post(BASE_URL, json=data, headers=get_headers())
        response.raise_for_status()
        result = response.json()[0]
        return enrich_prompt(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(prompt_id: str):
    try:
        response = requests.get(f"{BASE_URL}?id=eq.{prompt_id}", headers=get_headers())
        response.raise_for_status()
        data = response.json()
        if not data:
            raise HTTPException(status_code=404, detail="Prompt not found")
        return enrich_prompt(data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(prompt_id: str, prompt: PromptUpdate):
    try:
        data = prompt.model_dump(exclude_unset=True)
        data["updated_at"] = datetime.utcnow().isoformat()
        
        response = requests.patch(f"{BASE_URL}?id=eq.{prompt_id}", json=data, headers=get_headers())
        response.raise_for_status()
        result = response.json()
        if not result:
            raise HTTPException(status_code=404, detail="Prompt not found")
        return enrich_prompt(result[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{prompt_id}")
async def delete_prompt(prompt_id: str):
    try:
        response = requests.delete(f"{BASE_URL}?id=eq.{prompt_id}", headers=get_headers())
        response.raise_for_status()
        return {"deleted": True, "id": prompt_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
