"""
System API Schemas
"""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    timestamp: datetime
    components: dict[str, dict]


class SystemSettingCreate(BaseModel):
    setting_key: str = Field(..., pattern=r"^[A-Z_]+$", max_length=100)
    setting_value: str = Field(..., max_length=5000)
    setting_type: Literal["string", "integer", "boolean", "json", "password"] = "string"
    description: Optional[str] = Field(None, max_length=500)
    category: Literal["general", "collection", "security", "notification", "integration"] = "general"
    is_encrypted: bool = False


class SystemSettingUpdate(BaseModel):
    setting_value: str = Field(..., max_length=5000)
    is_active: Optional[bool] = None


class SystemSettingResponse(BaseModel):
    id: int
    setting_key: str
    setting_value: Optional[str] = None
    setting_type: str
    description: Optional[str] = None
    category: str
    is_encrypted: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DashboardStatsResponse(BaseModel):
    total_blacklist_ips: int
    total_whitelist_ips: int
    active_blacklist_ips: int
    today_new_ips: int
    countries_count: int
    source_breakdown: dict[str, int]
    recent_collections: list[dict]
    trend_data: Optional[list[dict]] = None


class AuditLogEntry(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    user: Optional[str] = None
    ip_address: Optional[str] = None
    details: Optional[dict[str, Any]] = None
    timestamp: datetime


class APIErrorResponse(BaseModel):
    success: Literal[False] = False
    error: str
    code: str
    details: Optional[dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class APISuccessResponse(BaseModel):
    success: Literal[True] = True
    data: Any
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
