from datetime import datetime

from .base_model import BaseModel


class ListFiles(BaseModel):
    files: "ListFilesFiles"


class ListFilesFiles(BaseModel):
    objects: list["ListFilesFilesObjects"]


class ListFilesFilesObjects(BaseModel):
    file_name: str
    updated_at: datetime


ListFiles.update_forward_refs()
ListFilesFiles.update_forward_refs()
ListFilesFilesObjects.update_forward_refs()
