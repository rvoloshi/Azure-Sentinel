from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class MatchingVM(BaseModel):
    _id: str
    name: str

    class Config:
        extra = "ignore"


class Criterion(BaseModel):
    argument: str
    case_sensitive: bool
    field: str
    matching_vms: List[MatchingVM]
    op: str

    class Config:
        extra = "ignore"


class Asset(BaseModel):
    id: str
    labels: List[str]
    metadata: Dict[str, Any] = {}
    name: str

    class Config:
        extra = "ignore"


class GuardicoreLabelGroup(BaseModel):
    _id: str
    id: str
    key: str
    value: str
    added_assets: List[Asset]
    added_assets_counter: int
    dynamic_criteria: List[Criterion]
    dynamic_criteria_counter: int
    equal_criteria: List[Criterion]
    implicit_criteria: List[Criterion]
    matched_assets: List[Asset]
    matched_assets_counter: int
    rules_with_label: int

    class Config:
        extra = "ignore"