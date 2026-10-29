from .base_model import BaseModel


class TestingAcknowledgeEvent(BaseModel):
    event_acknowledge: bool


TestingAcknowledgeEvent.update_forward_refs()
