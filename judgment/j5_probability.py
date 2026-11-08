import random
from typing import Dict, Any, Tuple
from contracts.command import Attempt
from contracts.probability import ProbabilityAudit

class ProbabilityEngine:
    """
    概率裁定引擎 (J5)。
    负责根据当前世界状态计算概率，并使用本地随机流抽样。
    绝对不使用 AI 来评估概率。
    """

    @classmethod
    def resolve(cls, attempt: Attempt, world_snapshot: Dict[str, Any], seed: str) -> Tuple[bool, ProbabilityAudit]:
        """
        计算动作的成功率并执行抽样。
        返回：(是否成功, 审计记录)
        """
        # 锁定随机流，保证同一种子下结果可复现
        rng = random.Random(seed)
        
        base_p = 0.5
        modifiers = {}

        # 1. 根据动作类型设定基础概率
        if attempt.type == "persuade":
            base_p = 0.4
        elif attempt.type == "intimidate":
            base_p = 0.6
        elif attempt.type == "bribe":
            base_p = 0.8
        elif attempt.type == "cover_up":  # 掩盖事实
            base_p = 0.3
        elif attempt.type == "extreme_action":
            # 极端动作（如掏枪、殴打）通常不靠概率，而是看硬约束
            # 但如果走到了这里，说明硬约束通过了，现在判定是否命中
            base_p = 0.9

        # 2. 根据世界状态（World Snapshot）进行修正
        actor_id = world_snapshot.get("current_command_actor")
        actor_stats = world_snapshot.get("actors", {}).get(actor_id, {})
        target = world_snapshot.get("entities", {}).get(attempt.target_id, {})

        # 如果玩家在这个 NPC 面前有威信（职级压制）
        if actor_stats.get("rank", 0) > target.get("rank", 0):
            modifiers["rank_suppression"] = 0.15

        # 如果目标处于极度恐惧或崩溃状态
        if target.get("mental_state") == "terrified":
            modifiers["target_terrified"] = 0.2
            
        # 如果目标生性多疑，且动作是掩盖事实
        if target.get("traits", {}).get("suspicious") and attempt.type == "cover_up":
            modifiers["target_suspicious"] = -0.2

        # 3. 计算最终概率 (限制在 0.05 到 0.95 之间，避免绝对成功或失败)
        final_p = base_p + sum(modifiers.values())
        final_p = max(0.05, min(0.95, final_p))

        # 4. 掷骰子
        roll = rng.random()
        is_success = roll <= final_p

        # 5. 生成审计记录
        audit = ProbabilityAudit(
            action_type=attempt.type,
            base_probability=base_p,
            modifiers=modifiers,
            final_probability=final_p,
            roll_value=roll,
            is_success=is_success,
            rng_seed=seed
        )

        return is_success, audit