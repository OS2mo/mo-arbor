from uuid import UUID

from .base_model import BaseModel


class ListRootUnits(BaseModel):
    org_units: "ListRootUnitsOrgUnits"


class ListRootUnitsOrgUnits(BaseModel):
    objects: list["ListRootUnitsOrgUnitsObjects"]


class ListRootUnitsOrgUnitsObjects(BaseModel):
    uuid: UUID
    validities: list["ListRootUnitsOrgUnitsObjectsValidities"]


class ListRootUnitsOrgUnitsObjectsValidities(BaseModel):
    user_key: str


ListRootUnits.update_forward_refs()
ListRootUnitsOrgUnits.update_forward_refs()
ListRootUnitsOrgUnitsObjects.update_forward_refs()
ListRootUnitsOrgUnitsObjectsValidities.update_forward_refs()
