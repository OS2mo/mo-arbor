from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from .base_model import BaseModel


class ListUnitHistories(BaseModel):
    org_units: "ListUnitHistoriesOrgUnits"


class ListUnitHistoriesOrgUnits(BaseModel):
    objects: list["ListUnitHistoriesOrgUnitsObjects"]
    page_info: "ListUnitHistoriesOrgUnitsPageInfo"


class ListUnitHistoriesOrgUnitsObjects(BaseModel):
    uuid: UUID
    validities: list["ListUnitHistoriesOrgUnitsObjectsValidities"]


class ListUnitHistoriesOrgUnitsObjectsValidities(BaseModel):
    user_key: str
    name: str
    validity: "ListUnitHistoriesOrgUnitsObjectsValiditiesValidity"


class ListUnitHistoriesOrgUnitsObjectsValiditiesValidity(BaseModel):
    from_: datetime = Field(alias="from")
    to: datetime | None


class ListUnitHistoriesOrgUnitsPageInfo(BaseModel):
    next_cursor: Any | None


ListUnitHistories.update_forward_refs()
ListUnitHistoriesOrgUnits.update_forward_refs()
ListUnitHistoriesOrgUnitsObjects.update_forward_refs()
ListUnitHistoriesOrgUnitsObjectsValidities.update_forward_refs()
ListUnitHistoriesOrgUnitsObjectsValiditiesValidity.update_forward_refs()
ListUnitHistoriesOrgUnitsPageInfo.update_forward_refs()
