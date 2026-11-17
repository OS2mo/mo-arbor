from uuid import UUID

from .base_model import BaseModel


class TestingRelateUnits(BaseModel):
    related_units_update: "TestingRelateUnitsRelatedUnitsUpdate"


class TestingRelateUnitsRelatedUnitsUpdate(BaseModel):
    uuid: UUID


TestingRelateUnits.update_forward_refs()
TestingRelateUnitsRelatedUnitsUpdate.update_forward_refs()
