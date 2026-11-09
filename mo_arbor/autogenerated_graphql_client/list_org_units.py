from datetime import datetime
from typing import Any
from typing import Optional
from uuid import UUID

from pydantic import Field

from .base_model import BaseModel


class ListOrgUnits(BaseModel):
    org_units: "ListOrgUnitsOrgUnits"


class ListOrgUnitsOrgUnits(BaseModel):
    objects: list["ListOrgUnitsOrgUnitsObjects"]
    page_info: "ListOrgUnitsOrgUnitsPageInfo"


class ListOrgUnitsOrgUnitsObjects(BaseModel):
    uuid: UUID
    validities: list["ListOrgUnitsOrgUnitsObjectsValidities"]


class ListOrgUnitsOrgUnitsObjectsValidities(BaseModel):
    user_key: str
    parent_response: Optional["ListOrgUnitsOrgUnitsObjectsValiditiesParentResponse"]
    validity: "ListOrgUnitsOrgUnitsObjectsValiditiesValidity"


class ListOrgUnitsOrgUnitsObjectsValiditiesParentResponse(BaseModel):
    uuid: UUID


class ListOrgUnitsOrgUnitsObjectsValiditiesValidity(BaseModel):
    from_: datetime = Field(alias="from")


class ListOrgUnitsOrgUnitsPageInfo(BaseModel):
    next_cursor: Any | None


ListOrgUnits.update_forward_refs()
ListOrgUnitsOrgUnits.update_forward_refs()
ListOrgUnitsOrgUnitsObjects.update_forward_refs()
ListOrgUnitsOrgUnitsObjectsValidities.update_forward_refs()
ListOrgUnitsOrgUnitsObjectsValiditiesParentResponse.update_forward_refs()
ListOrgUnitsOrgUnitsObjectsValiditiesValidity.update_forward_refs()
ListOrgUnitsOrgUnitsPageInfo.update_forward_refs()
