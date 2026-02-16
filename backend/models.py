from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

class Platform(str, Enum):
    telegram = "telegram"
    linkedin = "linkedin"
    vk = "vk"

class PostStatus(str, Enum):
    draft = "draft"
    scheduled = "scheduled"
    published = "published"
    failed = "failed"

class PostCreate(BaseModel):
    content: str
    platform: Platform
    scheduled_at: datetime
    channel_id: Optional[str] = None

class PostUpdate(BaseModel):
    content: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[PostStatus] = None

class PostResponse(BaseModel):
    id: str
    content: str
    platform: Platform
    status: PostStatus
    scheduled_at: datetime
    published_at: Optional[datetime] = None
    created_at: datetime
    utm_tag: Optional[str] = None

class AccountCreate(BaseModel):
    platform: Platform
    token: str
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None

class AccountResponse(BaseModel):
    id: str
    platform: Platform
    channel_name: Optional[str]
    is_active: bool
    connected_at: datetime
