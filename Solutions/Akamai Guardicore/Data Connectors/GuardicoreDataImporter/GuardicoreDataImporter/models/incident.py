import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field, field_validator


class Asset(BaseModel):
    ip: str
    vm_id: Optional[str] = None
    vm: Optional[dict[str, Any]] = None
    is_inner: bool

    class Config:
        extra = "ignore"


class GuardicoreIncident(BaseModel):
    id: str = Field(alias='_id')
    sensor_type: str
    TimeGenerated: str = Field(alias='start_time')
    end_time: int
    last_updated_time: int
    ended: bool
    severity: int
    affected_assets: list[Asset]
    enriched: bool
    reenrich_count: int
    similarity_calculated: bool
    is_experimental: bool
    original_id: str
    experimental_id: str
    policy_revision: int
    incident_type: str
    has_export: bool
    direction: str
    source_asset: Asset
    destination_asset: Asset

    @field_validator('TimeGenerated', mode="before")
    def start_time_validator(cls, value: int) -> str:
        return datetime.datetime.fromtimestamp(int(value) // 1000, tz=datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    class Config:
        extra = "ignore"
