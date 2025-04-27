from typing import Optional

from pydantic import BaseModel, field_validator, Field


class GuardicoreConnection(BaseModel):
    id: Optional[str] = Field(alias="flow_id")
    connection_type: str
    count: int = Field(alias="flow_count")
    ip_protocol: str
    has_mismatch_alert: Optional[bool] = False
    connector_dest_rule_id: Optional[str] = ""
    connector_source_rule_id: Optional[str] = ""
    slot_start_time: int
    original_policy_verdict: Optional[str] = ""
    policy_rule: str
    policy_ruleset: Optional[str] = ""
    policy_verdict: str
    source_ip: str
    source_node_id: str
    source_node_type: str
    source_process: str
    source_process_full_path: Optional[str] = ""
    source_process_hash: Optional[str] = ""
    source_process_id: Optional[str] = ""
    source_process_name: Optional[str] = ""
    source_windows_service_display_name: Optional[str] = ""
    source_windows_service_name: Optional[str] = ""
    destination_asset_hash: Optional[int] = None
    destination_ip: str
    destination_node_id: str
    destination_node_type: str
    destination_port: int
    destination_process: Optional[str] = ""
    destination_process_id: Optional[str] = ""
    destination_process_name: Optional[str] = ""
    destination_windows_service_display_name: Optional[str] = ""
    destination_windows_service_name: Optional[str] = ""
    violates_policy: bool
    is_corporate: Optional[bool] = False
    source_container_labels: Optional[List[str]] = Field(default_factory=list)
    destination_container_labels: Optional[List[str]] = Field(default_factory=list)
    source_kubernetes_labels: Optional[List[str]] = Field(default_factory=list)
    destination_kubernetes_labels: Optional[List[str]] = Field(default_factory=list)

    @field_validator('slot_start_time', mode='before')
    def change_slot_start_time(cls, value: float) -> int:
        return int(value)

    class Config:
        extra = "ignore"
