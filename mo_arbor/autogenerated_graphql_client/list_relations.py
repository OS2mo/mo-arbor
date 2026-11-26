from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from .base_model import BaseModel


class ListRelations(BaseModel):
    related_units: "ListRelationsRelatedUnits"


class ListRelationsRelatedUnits(BaseModel):
    objects: list["ListRelationsRelatedUnitsObjects"]
    page_info: "ListRelationsRelatedUnitsPageInfo"


class ListRelationsRelatedUnitsObjects(BaseModel):
    validities: list["ListRelationsRelatedUnitsObjectsValidities"]


class ListRelationsRelatedUnitsObjectsValidities(BaseModel):
    validity: "ListRelationsRelatedUnitsObjectsValiditiesValidity"
    org_units_response: "ListRelationsRelatedUnitsObjectsValiditiesOrgUnitsResponse"


class ListRelationsRelatedUnitsObjectsValiditiesValidity(BaseModel):
    from_: datetime = Field(alias="from")
    to: datetime | None


class ListRelationsRelatedUnitsObjectsValiditiesOrgUnitsResponse(BaseModel):
    objects: list["ListRelationsRelatedUnitsObjectsValiditiesOrgUnitsResponseObjects"]


class ListRelationsRelatedUnitsObjectsValiditiesOrgUnitsResponseObjects(BaseModel):
    uuid: UUID


class ListRelationsRelatedUnitsPageInfo(BaseModel):
    next_cursor: Any | None


ListRelations.update_forward_refs()
ListRelationsRelatedUnits.update_forward_refs()
ListRelationsRelatedUnitsObjects.update_forward_refs()
ListRelationsRelatedUnitsObjectsValidities.update_forward_refs()
ListRelationsRelatedUnitsObjectsValiditiesValidity.update_forward_refs()
ListRelationsRelatedUnitsObjectsValiditiesOrgUnitsResponse.update_forward_refs()
ListRelationsRelatedUnitsObjectsValiditiesOrgUnitsResponseObjects.update_forward_refs()
ListRelationsRelatedUnitsPageInfo.update_forward_refs()
