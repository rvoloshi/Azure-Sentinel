from typing import Optional, Any

from pydantic import BaseModel, Field


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
    start_time: int
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

    class Config:
        extra = "ignore"
