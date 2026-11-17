from typing import Any
from typing import Optional
from uuid import UUID

from .base_model import BaseModel


class ListReportUnits(BaseModel):
    org_units: "ListReportUnitsOrgUnits"


class ListReportUnitsOrgUnits(BaseModel):
    objects: list["ListReportUnitsOrgUnitsObjects"]
    page_info: "ListReportUnitsOrgUnitsPageInfo"


class ListReportUnitsOrgUnitsObjects(BaseModel):
    uuid: UUID
    current: Optional["ListReportUnitsOrgUnitsObjectsCurrent"]


class ListReportUnitsOrgUnitsObjectsCurrent(BaseModel):
    user_key: str
    name: str


class ListReportUnitsOrgUnitsPageInfo(BaseModel):
    next_cursor: Any | None


ListReportUnits.update_forward_refs()
ListReportUnitsOrgUnits.update_forward_refs()
ListReportUnitsOrgUnitsObjects.update_forward_refs()
ListReportUnitsOrgUnitsObjectsCurrent.update_forward_refs()
ListReportUnitsOrgUnitsPageInfo.update_forward_refs()
