from .base_model import BaseModel


class TestingListEvents(BaseModel):
    events: "TestingListEventsEvents"


class TestingListEventsEvents(BaseModel):
    objects: list["TestingListEventsEventsObjects"]


class TestingListEventsEventsObjects(BaseModel):
    subject: str


TestingListEvents.update_forward_refs()
TestingListEventsEvents.update_forward_refs()
TestingListEventsEventsObjects.update_forward_refs()
