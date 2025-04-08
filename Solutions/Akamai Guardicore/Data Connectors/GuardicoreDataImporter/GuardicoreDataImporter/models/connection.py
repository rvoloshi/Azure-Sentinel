import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class GuardicoreConnection(BaseModel):
    id: str
    connection_type: str
    count: int
    incidents: bool
    ip_protocol: str
    has_mismatch_alert: bool
    connector_dest_rule_id: Optional[str]
    connector_source_rule_id: Optional[str]
    TimeGenerated: str = Field(alias='slot_start_time')
    original_policy_verdict: str
    policy_rule: str
    policy_ruleset: Optional[str]
    policy_verdict: str
    source_ip: str
    source_node_id: str
    source_node_type: str
    source_process: str
    source_process_full_path: str
    source_process_hash: str
    source_process_id: str
    source_process_name: str
    source_windows_service_display_name: Optional[str]
    source_windows_service_name: Optional[str]
    destination_asset_hash: int
    destination_ip: str
    destination_node_id: str
    destination_node_type: str
    destination_port: int
    destination_process: str
    destination_process_id: str
    destination_process_name: str
    destination_windows_service_display_name: Optional[str]
    destination_windows_service_name: Optional[str]
    violates_policy: bool

    @field_validator('TimeGenerated', mode="before")
    def slot_start_time_validator(cls, value: int) -> str:
        return datetime.datetime.fromtimestamp(int(value) // 1000, tz=datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    class Config:
        extra = "ignore"
