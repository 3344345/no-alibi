from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Dict, Any, Optional
from contracts.command import Command, Attempt
from contracts.event import CommittedEvent
from contracts.resolution import AttemptResult

class HandlerResult(BaseModel):
    attempt_result: AttemptResult
    event: Optional[CommittedEvent] = None
    state_changes: Dict[str, Any] = {}

class ActionHandler(ABC):
    @abstractmethod
    def handle(self, attempt: Attempt, command: Command, world_snapshot: Dict[str, Any], seed: str, sequence: int) -> HandlerResult:
        pass