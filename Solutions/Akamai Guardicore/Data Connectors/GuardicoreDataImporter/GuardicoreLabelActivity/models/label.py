from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class LabelAsset(BaseModel):
    hw_uuid: Optional[str] = ""
    bios_uuid: Optional[str] = ""
    id: str
    orchestration_details: Optional[List[Dict[str, Any]]] = []
    name: str
    labels: Optional[List[str]] = []
    nics: List[Dict[str, Any]]
    ip_addresses: List[str]
    guest_agent_details: Optional[Dict[str, Any]] = {}
    metadata: Optional[Dict[str, Any]] = {}
    label_groups: Optional[List[str]] = []


class LabelCriteria(BaseModel):
    argument: str
    source: str
    op: str
    field: str
    id: str
    label_id: str


class GuardicoreLabel(BaseModel):
    sampling_timestamp: int
    static_criteria: Optional[List[LabelCriteria]] = []
    value: Optional[str] = ""
    dynamic_criteria_counter: Optional[int] = 0
    dynamic_criteria: Optional[List[LabelCriteria]] = []
    static_assets: Optional[List[LabelAsset]] = []
    dynamic_assets_counter: Optional[int] = 0
    id: str
    key: str
    dynamic_assets: Optional[List[LabelAsset]] = []
    static_criteria_counter: Optional[int] = 0
    implicit_criteria: Optional[List[LabelCriteria]] = []
    rules_with_label: Optional[int] = 0
    static_assets_counter: Optional[int] = 0
    name: Optional[str] = ""
    color_index: Optional[int] = 0

    class Config:
        extra = "ignore"
