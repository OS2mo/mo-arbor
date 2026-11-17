from typing import Any
from typing import Optional
from uuid import UUID

from .base_model import BaseModel


class ListRelatedUnits(BaseModel):
    org_units: "ListRelatedUnitsOrgUnits"


class ListRelatedUnitsOrgUnits(BaseModel):
    objects: list["ListRelatedUnitsOrgUnitsObjects"]
    page_info: "ListRelatedUnitsOrgUnitsPageInfo"


class ListRelatedUnitsOrgUnitsObjects(BaseModel):
    uuid: UUID
    current: Optional["ListRelatedUnitsOrgUnitsObjectsCurrent"]


class ListRelatedUnitsOrgUnitsObjectsCurrent(BaseModel):
    user_key: str
    name: str
    related_units_response: "ListRelatedUnitsOrgUnitsObjectsCurrentRelatedUnitsResponse"


class ListRelatedUnitsOrgUnitsObjectsCurrentRelatedUnitsResponse(BaseModel):
    objects: list["ListRelatedUnitsOrgUnitsObjectsCurrentRelatedUnitsResponseObjects"]


class ListRelatedUnitsOrgUnitsObjectsCurrentRelatedUnitsResponseObjects(BaseModel):
    current: Optional[
        "ListRelatedUnitsOrgUnitsObjectsCurrentRelatedUnitsResponseObjectsCurrent"
    ]


class ListRelatedUnitsOrgUnitsObjectsCurrentRelatedUnitsResponseObjectsCurrent(
    BaseModel
):
    org_units_response: "ListRelatedUnitsOrgUnitsObjectsCurrentRelatedUnitsResponseObjectsCurrentOrgUnitsResponse"


class ListRelatedUnitsOrgUnitsObjectsCurrentRelatedUnitsResponseObjectsCurrentOrgUnitsResponse(
    BaseModel
):
    objects: list[
        "ListRelatedUnitsOrgUnitsObjectsCurrentRelatedUnitsResponseObjectsCurrentOrgUnitsResponseObjects"
    ]


class ListRelatedUnitsOrgUnitsObjectsCurrentRelatedUnitsResponseObjectsCurrentOrgUnitsResponseObjects(
    BaseModel
):
    uuid: UUID


class ListRelatedUnitsOrgUnitsPageInfo(BaseModel):
    next_cursor: Any | None


ListRelatedUnits.update_forward_refs()
ListRelatedUnitsOrgUnits.update_forward_refs()
ListRelatedUnitsOrgUnitsObjects.update_forward_refs()
ListRelatedUnitsOrgUnitsObjectsCurrent.update_forward_refs()
ListRelatedUnitsOrgUnitsObjectsCurrentRelatedUnitsResponse.update_forward_refs()
ListRelatedUnitsOrgUnitsObjectsCurrentRelatedUnitsResponseObjects.update_forward_refs()
ListRelatedUnitsOrgUnitsObjectsCurrentRelatedUnitsResponseObjectsCurrent.update_forward_refs()
ListRelatedUnitsOrgUnitsObjectsCurrentRelatedUnitsResponseObjectsCurrentOrgUnitsResponse.update_forward_refs()
ListRelatedUnitsOrgUnitsObjectsCurrentRelatedUnitsResponseObjectsCurrentOrgUnitsResponseObjects.update_forward_refs()
ListRelatedUnitsOrgUnitsPageInfo.update_forward_refs()
