from .base_model import BaseModel


class ReadFile(BaseModel):
    files: "ReadFileFiles"


class ReadFileFiles(BaseModel):
    objects: list["ReadFileFilesObjects"]


class ReadFileFilesObjects(BaseModel):
    base64_contents: str


ReadFile.update_forward_refs()
ReadFileFiles.update_forward_refs()
ReadFileFilesObjects.update_forward_refs()
