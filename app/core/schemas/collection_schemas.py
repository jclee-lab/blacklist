"""
Collection API Schemas
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class CollectionTriggerRequest(BaseModel):
    source: Literal["REGTECH", "SECUDIUM", "ALL"] = "ALL"
    force: bool = False


class CollectionStatusResponse(BaseModel):
    source: str
    status: Literal["idle", "running", "completed", "failed"]
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    collected_count: int = 0
    error_message: Optional[str] = None


class CollectionHistoryItem(BaseModel):
    id: int
    source: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    collected_count: int = 0
    error_message: Optional[str] = None


class CollectionStatsResponse(BaseModel):
    total_ips: int
    regtech_count: int
    secudium_count: int
    manual_count: int
    active_count: int
    inactive_count: int
    last_collection: Optional[datetime] = None
    countries: list[dict]


class CredentialUpdateRequest(BaseModel):
    service_name: Literal["REGTECH", "SECUDIUM"]
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=500)
    enabled: bool = True
    collection_interval: Literal["hourly", "daily", "weekly", "manual"] = "daily"


class CredentialTestResponse(BaseModel):
    success: bool
    message: str
    tested_at: datetime
    response_time_ms: Optional[int] = None
