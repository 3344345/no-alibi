from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal
from contracts.event import CommittedEvent

class AttemptResult(BaseModel):
    attempt_id: str
    status: Literal["success", "failed", "partial_success", "pending", "invalid", "cancelled"]
    reason_code: str = ""
    description: str = ""

class Resolution(BaseModel):
    command_id: str
    attempt_results: List[AttemptResult] = Field(default_factory=list)
    generated_events: List[CommittedEvent] = Field(default_factory=list)
    state_changes: Dict[str, Any] = Field(default_factory=dict)
    pending_observations: List[Dict[str, Any]] = Field(default_factory=list)