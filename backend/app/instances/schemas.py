"""Instance request/response schemas."""
from datetime import datetime
from pydantic import BaseModel


class InstanceResponse(BaseModel):
    id: str
    status: str
    domain: str | None
    ip_address: str | None
    gateway_token: str | None
    gemini_api_key_set: bool = False
    created_at: datetime
    last_heartbeat: datetime | None

    class Config:
        from_attributes = True


class InstanceUpdate(BaseModel):
    gemini_api_key: str | None = None
