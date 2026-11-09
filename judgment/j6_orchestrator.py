from typing import Dict, Any
from contracts.command import Command
from contracts.resolution import Resolution, AttemptResult
from judgment.handler_base import ActionHandler
from judgment.j2_constraints import ConstraintValidator
from judgment.j5_probability import ProbabilityEngine

# 插件注册表 (开闭原则核心)
from judgment.handlers.career_handler import CareerHandler

HANDLER_REGISTRY: Dict[str, ActionHandler] = {
    "evaluate_vacancy": CareerHandler(),
}

class ActionOrchestrator:
    @classmethod
    def process(cls, command: Command, world_snapshot: Dict[str, Any], seed: str) -> Resolution:
        resolution = Resolution(command_id=command.command_id)
        current_seq = world_snapshot.get("last_sequence", 1000)

        for attempt in command.attempts:
            current_seq += 1
            
            # 路由到专属业务插件
            if attempt.type in HANDLER_REGISTRY:
                handler = HANDLER_REGISTRY[attempt.type]
                result = handler.handle(attempt, command, world_snapshot, seed, current_seq)
                
                resolution.attempt_results.append(result.attempt_result)
                if result.event:
                    resolution.generated_events.append(result.event)
                resolution.state_changes.update(result.state_changes)
                continue

            # 常规动作：硬约束 + 概率引擎
            constraint_res = ConstraintValidator.validate(attempt, world_snapshot)
            if not constraint_res.is_valid:
                resolution.attempt_results.append(AttemptResult(
                    attempt_id=attempt.attempt_id, status="failed",
                    reason_code=constraint_res.error_code.value, description=constraint_res.error_message
                ))
                continue

            is_success, prob_audit = ProbabilityEngine.resolve(attempt, world_snapshot, seed)
            event_type = f"{attempt.type}_{'success' if is_success else 'failed'}"
            
            resolution.attempt_results.append(AttemptResult(
                attempt_id=attempt.attempt_id, status="success" if is_success else "failed"
            ))
            resolution.generated_events.append(CommittedEvent(
                event_id=f"evt_{seed[:8]}_{current_seq}", command_id=command.command_id,
                sequence=current_seq, world_time=command.world_time, actor_id=command.actor_id,
                event_type=event_type, payload={"audit": prob_audit.model_dump()},
                rule_version="v2.0", is_failure=not is_success
            ))

        return resolution