from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime

class CommittedEvent(BaseModel):
    event_id: str
    command_id: str
    sequence: int
    world_time: datetime
    actor_id: str
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    caused_by: List[str] = Field(default_factory=list)
    rule_version: str
    is_failure: bool = False