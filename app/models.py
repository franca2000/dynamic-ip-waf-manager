from pydantic import BaseModel, Field, IPvAnyAddress, field_validator
from typing import Optional, Literal
from datetime import datetime

class IPEntry(BaseModel):
    """
    Model to receive a block/allow request.
    """
    ip: IPvAnyAddress = Field(..., description="Valid IPv4 or IPv6 address")
    action: Literal['ALLOW', 'BLOCK'] = Field(..., description="Action to take")
    context: str = Field(..., min_length=3, description="Environment or Client ID (e.g., 'prod', 'merchant-123')")
    comment: Optional[str] = Field(None, max_length=200, description="Reason for the change")
    ttl_seconds: Optional[int] = Field(None, gt=0, description="Time to live in seconds. Null = Permanent")

    # Internal fields (not sent by the user, generated automatically)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class IPResponse(IPEntry):
    """
    Model for client response, includes calculated data.
    """
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class IPSearch(BaseModel):
    """Search filters"""
    context: Optional[str] = None
    action: Optional[str] = None