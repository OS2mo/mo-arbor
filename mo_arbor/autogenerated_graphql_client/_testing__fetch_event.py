from typing import Any
from typing import Optional

from .base_model import BaseModel


class TestingFetchEvent(BaseModel):
    event_fetch: Optional["TestingFetchEventEventFetch"]


class TestingFetchEventEventFetch(BaseModel):
    subject: str
    token: Any


TestingFetchEvent.update_forward_refs()
TestingFetchEventEventFetch.update_forward_refs()
