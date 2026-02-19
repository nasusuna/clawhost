"""Instance request/response schemas."""
from datetime import datetime
from pydantic import BaseModel


class InstanceResponse(BaseModel):
    id: str
    status: str
    domain: str | None
    ip_address: str | None
    gateway_token: str | None
    created_at: datetime
    last_heartbeat: datetime | None

    class Config:
        from_attributes = True
