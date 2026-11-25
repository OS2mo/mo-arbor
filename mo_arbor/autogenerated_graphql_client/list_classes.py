from .base_model import BaseModel


class ListClasses(BaseModel):
    classes: "ListClassesClasses"


class ListClassesClasses(BaseModel):
    objects: list["ListClassesClassesObjects"]


class ListClassesClassesObjects(BaseModel):
    validities: list["ListClassesClassesObjectsValidities"]


class ListClassesClassesObjectsValidities(BaseModel):
    user_key: str


ListClasses.update_forward_refs()
ListClassesClasses.update_forward_refs()
ListClassesClassesObjects.update_forward_refs()
ListClassesClassesObjectsValidities.update_forward_refs()
