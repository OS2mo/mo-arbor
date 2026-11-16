from typing import Optional

from .base_model import BaseModel


class ListClasses(BaseModel):
    classes: "ListClassesClasses"


class ListClassesClasses(BaseModel):
    objects: list["ListClassesClassesObjects"]


class ListClassesClassesObjects(BaseModel):
    current: Optional["ListClassesClassesObjectsCurrent"]


class ListClassesClassesObjectsCurrent(BaseModel):
    user_key: str


ListClasses.update_forward_refs()
ListClassesClasses.update_forward_refs()
ListClassesClassesObjects.update_forward_refs()
ListClassesClassesObjectsCurrent.update_forward_refs()
