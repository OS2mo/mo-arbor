from datetime import datetime

from pydantic import Field

from .base_model import BaseModel


class TestingGetOrgUnitHistory(BaseModel):
    org_units: "TestingGetOrgUnitHistoryOrgUnits"


class TestingGetOrgUnitHistoryOrgUnits(BaseModel):
    objects: list["TestingGetOrgUnitHistoryOrgUnitsObjects"]


class TestingGetOrgUnitHistoryOrgUnitsObjects(BaseModel):
    validities: list["TestingGetOrgUnitHistoryOrgUnitsObjectsValidities"]


class TestingGetOrgUnitHistoryOrgUnitsObjectsValidities(BaseModel):
    name: str
    validity: "TestingGetOrgUnitHistoryOrgUnitsObjectsValiditiesValidity"


class TestingGetOrgUnitHistoryOrgUnitsObjectsValiditiesValidity(BaseModel):
    from_: datetime = Field(alias="from")
    to: datetime | None


TestingGetOrgUnitHistory.update_forward_refs()
TestingGetOrgUnitHistoryOrgUnits.update_forward_refs()
TestingGetOrgUnitHistoryOrgUnitsObjects.update_forward_refs()
TestingGetOrgUnitHistoryOrgUnitsObjectsValidities.update_forward_refs()
TestingGetOrgUnitHistoryOrgUnitsObjectsValiditiesValidity.update_forward_refs()
