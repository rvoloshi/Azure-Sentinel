from typing import List
from pydantic import BaseModel, Field


class Label(BaseModel):
    id: str
    key: str
    value: str
    name: str
    color_index: int

class LabelGroup(BaseModel):
    id: str
    name: str


class GuardicoreAsset(BaseModel):
    id: str = Field(alias="_id")
    active: bool
    bios_uuid: str
    component_cluster_id: str
    doc_version: int
    first_seen: int
    hw_uuid: str
    is_agent_installed: bool
    is_foreign: bool
    is_on: bool
    label_groups: List[LabelGroup]
    last_guest_agent_details_update: int
    last_seen: int
    name: str
    replicated_labels: List[str]
    revision: int
    sync_revision: int
    vm_name: str
    vm_id: str
    ip_addresses: List[str]
    mac_addresses: List[str]
    full_name: str
    status: str
    comments: str
    agent_id: str
    labels: List[Label]

    class Config:
        extra = "ignore"