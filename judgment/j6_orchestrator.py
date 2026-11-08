import uuid
from datetime import datetime
from typing import Dict, Any, List
from contracts.command import Command, Attempt
from contracts.resolution import Resolution, AttemptResult
from contracts.event import CommittedEvent
from contracts.errors import ConstraintErrorCode
from judgment.j2_constraints import ConstraintValidator
from judgment.j5_probability import ProbabilityEngine

class ActionOrchestrator:
    """
    后果编排引擎 (J6)。
    负责串联硬约束、概率计算，并生成最终的事件与状态变更计划。
    绝不在这里直接写数据库。
    """
    
    @classmethod
    def process(cls, command: Command, world_snapshot: Dict[str, Any], seed: str) -> Resolution:
        resolution = Resolution(
            command_id=command.command_id,
            attempt_results=[],
            generated_events=[],
            state_changes={},
            pending_observations=[]
        )
        
        # 获取当前世界的时间序列水位，用于生成新事件的 sequence
        current_seq = world_snapshot.get("last_sequence", 1000)

        # 遍历命令中的每一个子动作
        for attempt in command.attempts:
            current_seq += 1
            
            # 1. 跑硬约束 (J2)
            constraint_res = ConstraintValidator.validate(attempt, world_snapshot)
            
            if not constraint_res.is_valid:
                # 校验失败，生成一个可见的“失败事实”（如果动作是可见的）
                resolution.attempt_results.append(AttemptResult(
                    attempt_id=attempt.attempt_id,
                    status="failed",
                    reason_code=constraint_res.error_code.value if constraint_res.error_code else "UNKNOWN",
                    description=constraint_res.error_message or "动作因物理/制度限制而失败。"
                ))
                
                # 如果有旁观者，这里还应该生成 pending_observations
                # （此处省略旁观者检测逻辑，默认失败动作也会被在场的人看到）
                continue

            # 2. 跑概率与裁定 (J5)
            is_success, prob_audit = ProbabilityEngine.resolve(attempt, world_snapshot, seed)
            
            # 3. 根据判定结果生成事实事件 (CommittedEvent)
            event_id = f"evt_{uuid.uuid4().hex[:8]}"
            
            if is_success:
                status = "success"
                desc = f"动作 {attempt.type} 执行成功。"
                
                # 记录状态的改变（比如好感度提升、资金扣除）
                # 在实际游戏中，这里的 payload 会包含具体的数值变化
                new_event = CommittedEvent(
                    event_id=event_id,
                    command_id=command.command_id,
                    sequence=current_seq,
                    world_time=command.world_time,
                    actor_id=command.actor_id,
                    event_type=f"{attempt.type}_success",
                    payload={"target": attempt.target_id, "prob_audit": prob_audit.model_dump()},
                    caused_by=[],
                    rule_version="v2.0",
                    is_failure=False
                )
                resolution.generated_events.append(new_event)
                
                # 这里可以添加状态更新逻辑
                # resolution.state_changes[f"actors.{attempt.target_id}.relation"] = "+10"
                
            else:
                status = "failed"
                desc = f"尝试 {attempt.type} 失败。"
                
                new_event = CommittedEvent(
                    event_id=event_id,
                    command_id=command.command_id,
                    sequence=current_seq,
                    world_time=command.world_time,
                    actor_id=command.actor_id,
                    event_type=f"{attempt.type}_failed",
                    payload={"target": attempt.target_id, "prob_audit": prob_audit.model_dump()},
                    caused_by=[],
                    rule_version="v2.0",
                    is_failure=True
                )
                resolution.generated_events.append(new_event)

            # 写入子动作结果
            resolution.attempt_results.append(AttemptResult(
                attempt_id=attempt.attempt_id,
                status=status,
                description=desc
            ))

        return resolution