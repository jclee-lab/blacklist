"""
IP Management API Schemas
"""

import re
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class IPAddressBase(BaseModel):
    ip_address: str = Field(..., min_length=7, max_length=45)

    @field_validator("ip_address")
    @classmethod
    def validate_ip_format(cls, v: str) -> str:
        ipv4_pattern = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        cidr_pattern = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(/(3[0-2]|[12]?[0-9]))?$"
        if not (re.match(ipv4_pattern, v) or re.match(cidr_pattern, v)):
            raise ValueError("Invalid IP address format")
        return v


class BlacklistIPCreate(IPAddressBase):
    country: Optional[str] = Field(None, min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")
    reason: Optional[str] = Field(None, max_length=500)
    source: Literal["REGTECH", "SECUDIUM", "MANUAL"] = "MANUAL"
    detection_date: Optional[date] = None
    removal_date: Optional[date] = None
    confidence_level: Optional[int] = Field(None, ge=0, le=100)

    @field_validator("country", mode="before")
    @classmethod
    def uppercase_country(cls, v: Optional[str]) -> Optional[str]:
        return v.upper() if v else None

    @field_validator("removal_date")
    @classmethod
    def validate_removal_after_detection(cls, v: Optional[date], info) -> Optional[date]:
        if v and info.data.get("detection_date") and v < info.data["detection_date"]:
            raise ValueError("removal_date must be after detection_date")
        return v


class BlacklistIPUpdate(BaseModel):
    country: Optional[str] = Field(None, min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")
    reason: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    removal_date: Optional[date] = None
    confidence_level: Optional[int] = Field(None, ge=0, le=100)


class BlacklistIPResponse(IPAddressBase):
    id: int
    country: Optional[str] = None
    reason: Optional[str] = None
    source: str
    data_source: str
    is_active: bool
    detection_date: Optional[date] = None
    removal_date: Optional[date] = None
    confidence_level: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WhitelistIPCreate(IPAddressBase):
    country: Optional[str] = Field(None, min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")
    reason: Optional[str] = Field(None, max_length=500)
    source: Literal["MANUAL", "SYSTEM"] = "MANUAL"


class WhitelistIPResponse(IPAddressBase):
    id: int
    country: Optional[str] = None
    reason: Optional[str] = None
    source: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IPCheckRequest(BaseModel):
    ip: str = Field(..., min_length=7, max_length=45)
    ips: Optional[list[str]] = Field(None, max_length=100)

    @field_validator("ip")
    @classmethod
    def validate_single_ip(cls, v: str) -> str:
        ipv4_pattern = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        if not re.match(ipv4_pattern, v):
            raise ValueError("Invalid IP address format")
        return v


class IPCheckResponse(BaseModel):
    ip_address: str
    is_blacklisted: bool
    is_whitelisted: bool
    blacklist_info: Optional[dict] = None
    whitelist_info: Optional[dict] = None


class BulkIPCheckRequest(BaseModel):
    ips: list[str] = Field(..., min_length=1, max_length=1000)

    @field_validator("ips")
    @classmethod
    def validate_ips(cls, v: list[str]) -> list[str]:
        ipv4_pattern = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        invalid = [ip for ip in v if not re.match(ipv4_pattern, ip)]
        if invalid:
            raise ValueError(f"Invalid IP addresses: {invalid[:5]}")
        return v


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: Literal["asc", "desc"] = "desc"


class IPListResponse(BaseModel):
    data: list[BlacklistIPResponse]
    pagination: dict
    total: int
