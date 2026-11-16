from typing import Optional
from uuid import UUID

from .base_model import BaseModel


class TestingGetClassOwner(BaseModel):
    classes: "TestingGetClassOwnerClasses"


class TestingGetClassOwnerClasses(BaseModel):
    objects: list["TestingGetClassOwnerClassesObjects"]


class TestingGetClassOwnerClassesObjects(BaseModel):
    current: Optional["TestingGetClassOwnerClassesObjectsCurrent"]


class TestingGetClassOwnerClassesObjectsCurrent(BaseModel):
    owner: UUID | None


TestingGetClassOwner.update_forward_refs()
TestingGetClassOwnerClasses.update_forward_refs()
TestingGetClassOwnerClassesObjects.update_forward_refs()
TestingGetClassOwnerClassesObjectsCurrent.update_forward_refs()
