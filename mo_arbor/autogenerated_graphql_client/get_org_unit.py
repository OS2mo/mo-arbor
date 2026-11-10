from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from .base_model import BaseModel


class GetOrgUnit(BaseModel):
    org_units: "GetOrgUnitOrgUnits"


class GetOrgUnitOrgUnits(BaseModel):
    objects: list["GetOrgUnitOrgUnitsObjects"]


class GetOrgUnitOrgUnitsObjects(BaseModel):
    current: Optional["GetOrgUnitOrgUnitsObjectsCurrent"]
    validities: list["GetOrgUnitOrgUnitsObjectsValidities"]


class GetOrgUnitOrgUnitsObjectsCurrent(BaseModel):
    user_key: str
    name: str
    parent_response: Optional["GetOrgUnitOrgUnitsObjectsCurrentParentResponse"]
    unit_type_response: Optional["GetOrgUnitOrgUnitsObjectsCurrentUnitTypeResponse"]
    unit_level_response: Optional["GetOrgUnitOrgUnitsObjectsCurrentUnitLevelResponse"]


class GetOrgUnitOrgUnitsObjectsCurrentParentResponse(BaseModel):
    uuid: UUID


class GetOrgUnitOrgUnitsObjectsCurrentUnitTypeResponse(BaseModel):
    uuid: UUID


class GetOrgUnitOrgUnitsObjectsCurrentUnitLevelResponse(BaseModel):
    uuid: UUID


class GetOrgUnitOrgUnitsObjectsValidities(BaseModel):
    validity: "GetOrgUnitOrgUnitsObjectsValiditiesValidity"


class GetOrgUnitOrgUnitsObjectsValiditiesValidity(BaseModel):
    from_: datetime = Field(alias="from")
    to: datetime | None


GetOrgUnit.update_forward_refs()
GetOrgUnitOrgUnits.update_forward_refs()
GetOrgUnitOrgUnitsObjects.update_forward_refs()
GetOrgUnitOrgUnitsObjectsCurrent.update_forward_refs()
GetOrgUnitOrgUnitsObjectsCurrentParentResponse.update_forward_refs()
GetOrgUnitOrgUnitsObjectsCurrentUnitTypeResponse.update_forward_refs()
GetOrgUnitOrgUnitsObjectsCurrentUnitLevelResponse.update_forward_refs()
GetOrgUnitOrgUnitsObjectsValidities.update_forward_refs()
GetOrgUnitOrgUnitsObjectsValiditiesValidity.update_forward_refs()
