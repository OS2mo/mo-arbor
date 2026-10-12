from datetime import datetime

from pydantic import Field

from .base_model import BaseModel


class GetOrgUnitHistory(BaseModel):
    org_units: "GetOrgUnitHistoryOrgUnits"


class GetOrgUnitHistoryOrgUnits(BaseModel):
    objects: list["GetOrgUnitHistoryOrgUnitsObjects"]


class GetOrgUnitHistoryOrgUnitsObjects(BaseModel):
    validities: list["GetOrgUnitHistoryOrgUnitsObjectsValidities"]


class GetOrgUnitHistoryOrgUnitsObjectsValidities(BaseModel):
    name: str
    validity: "GetOrgUnitHistoryOrgUnitsObjectsValiditiesValidity"


class GetOrgUnitHistoryOrgUnitsObjectsValiditiesValidity(BaseModel):
    from_: datetime = Field(alias="from")
    to: datetime | None


GetOrgUnitHistory.update_forward_refs()
GetOrgUnitHistoryOrgUnits.update_forward_refs()
GetOrgUnitHistoryOrgUnitsObjects.update_forward_refs()
GetOrgUnitHistoryOrgUnitsObjectsValidities.update_forward_refs()
GetOrgUnitHistoryOrgUnitsObjectsValiditiesValidity.update_forward_refs()
