from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal
from datetime import datetime

class Attempt(BaseModel):
    attempt_id: str
    type: str
    target_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

class Command(BaseModel):
    command_id: str
    source: Literal["player", "npc", "system", "scheduler"]
    actor_id: str
    expected_revision: int
    world_time: datetime
    attempts: List[Attempt]