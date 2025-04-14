from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class Label(BaseModel):
    id: str
    key: str
    value: Optional[str] = ""
    name: str
    color_index: Optional[int] = 0


class LabelGroup(BaseModel):
    id: str
    name: str
    key: Optional[str] = ""
    value: Optional[str] = ""


class Capability(BaseModel):
    is_ok: bool
    name: str
    state: int
    text: str


class Aggregator(BaseModel):
    cluster_id: str
    component_id: str
    hostname: str


class AgentHealth(BaseModel):
    aggregator: Aggregator
    aggregator_component_id: str
    capabilities: List[Capability]
    status: str


class Health(BaseModel):
    controller: AgentHealth
    deception_agent: AgentHealth
    enforcement_agent: AgentHealth
    reveal_agent: AgentHealth


class StatusFlag(BaseModel):
    flag_type: str
    last_seen_time: bool


class GuardicoreAgent(BaseModel):
    sampling_timestamp: int
    id: str = Field(alias="_id")
    agent_id: Optional[str] = ""
    asset_id: Optional[str] = ""
    build_commit: Optional[str] = ""
    build_date: Optional[str] = ""
    component_id: Optional[str] = ""
    configuration_reported_errors: Optional[Dict[str, Dict[str, str]]] = {}
    configuration_reported_revision: Optional[int] = 0
    display_name: Optional[str] = ""
    doc_version: Optional[int] = 0
    first_seen: int
    health: Optional[Health] = None
    hostname: Optional[str] = ""
    installed_modules: Optional[List[str]] = []
    ip_addresses: List[str]
    is_agent_missing: Optional[bool] = False
    is_configuration_dirty: Optional[bool] = False
    is_missing: Optional[bool] = False
    kernel: Optional[str] = ""
    labels: List[Label]
    labels_groups: Optional[List[LabelGroup]] = []
    last_seen: int
    not_monitored: Optional[bool] = False
    os: Optional[str] = ""
    policy_revision: Optional[int] = 0
    status: str
    status_flags: Optional[List[StatusFlag]] = []
    supported_features: Optional[List[str]] = []
    version: Optional[str] = ""

    class Config:
        extra = "ignore"