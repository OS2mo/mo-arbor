from uuid import UUID

from .base_model import BaseModel


class TestingDeclareEventListener(BaseModel):
    event_listener_declare: "TestingDeclareEventListenerEventListenerDeclare"


class TestingDeclareEventListenerEventListenerDeclare(BaseModel):
    uuid: UUID


TestingDeclareEventListener.update_forward_refs()
TestingDeclareEventListenerEventListenerDeclare.update_forward_refs()
