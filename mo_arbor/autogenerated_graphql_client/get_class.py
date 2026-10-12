from uuid import UUID

from .base_model import BaseModel


class GetClass(BaseModel):
    classes: "GetClassClasses"


class GetClassClasses(BaseModel):
    objects: list["GetClassClassesObjects"]


class GetClassClassesObjects(BaseModel):
    uuid: UUID


GetClass.update_forward_refs()
GetClassClasses.update_forward_refs()
GetClassClassesObjects.update_forward_refs()
