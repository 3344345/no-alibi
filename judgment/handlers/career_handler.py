import uuid
from judgment.handler_base import ActionHandler, HandlerResult
from judgment.j7_career import CareerEngine
from contracts.resolution import AttemptResult
from contracts.event import CommittedEvent
from contracts.command import Command, Attempt

class CareerHandler(ActionHandler):
    def handle(self, attempt: Attempt, command: Command, world_snapshot: Dict[str, Any], seed: str, sequence: int) -> HandlerResult:
        actor_data = world_snapshot.get("actors", {}).get(command.actor_id, {})
        vacancy_info = {"max_age": 60, "min_tenure": 3}
        
        is_success, audit = CareerEngine.evaluate_promotion(actor_data, vacancy_info, seed)
        
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        state_changes = {}
        
        if is_success:
            res = AttemptResult(attempt_id=attempt.attempt_id, status="success", description="提拔考察通过。")
            state_changes = {
                f"actors.{command.actor_id}.rank": actor_data.get("rank", 1) + 1,
                f"actors.{command.actor_id}.tenure_years": 0,
                f"actors.{command.actor_id}.performance_score": 0
            }
            event = CommittedEvent(
                event_id=event_id, command_id=command.command_id, sequence=sequence,
                world_time=command.world_time, actor_id="system", event_type="promotion_success",
                payload={"audit": audit.model_dump() if audit else None},
                rule_version="v2.0", is_failure=False
            )
        else:
            res = AttemptResult(attempt_id=attempt.attempt_id, status="failed", description="提拔考察未通过。")
            event = CommittedEvent(
                event_id=event_id, command_id=command.command_id, sequence=sequence,
                world_time=command.world_time, actor_id="system", event_type="promotion_failed",
                payload={"audit": audit.model_dump() if audit else None},
                rule_version="v2.0", is_failure=True
            )
            
        return HandlerResult(attempt_result=res, event=event, state_changes=state_changes)