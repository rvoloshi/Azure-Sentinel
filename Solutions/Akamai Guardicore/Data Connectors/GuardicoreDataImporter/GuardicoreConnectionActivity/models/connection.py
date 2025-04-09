from typing import Optional

from pydantic import BaseModel


class GuardicoreConnection(BaseModel):
    id: str
    connection_type: str
    count: int
    ip_protocol: str
    has_mismatch_alert: bool
    connector_dest_rule_id: Optional[str]
    connector_source_rule_id: Optional[str]
    slot_start_time: int
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

    class Config:
        extra = "ignore"
