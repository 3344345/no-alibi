from typing import Dict, Any, Tuple, Optional
from contracts.probability import ProbabilityAudit
import random

class CareerEngine:
    """
    人事晋升判定引擎 (J7)。
    负责评估官员是否有资格晋升，并使用带权重的概率决定成败。
    """
    
    @classmethod
    def evaluate_promotion(cls, actor_data: Dict[str, Any], vacancy_info: Dict[str, Any], seed: str) -> Tuple[bool, Optional[ProbabilityAudit]]:
        age = actor_data.get("age", 30)
        tenure = actor_data.get("tenure_years", 0)
        performance = actor_data.get("performance_score", 50)
        risk = actor_data.get("hidden_risk", 0)
        patron = actor_data.get("patron_influence", 0)
        
        # --- 1. 硬约束（一票否决） ---
        if age > vacancy_info.get("max_age", 60):
            return False, None # 年龄到线，去人大养老
        if tenure < vacancy_info.get("min_tenure", 3):
            return False, None # 任期未满，被组织部驳回
        if risk > 70:
            return False, None # 纪委正在查你，绝不可能提拔

        # --- 2. 计算成功率（概率模型） ---
        base_p = 0.1 # 基础概率极低
        
        modifiers = {
            "performance_bonus": (performance / 100.0) * 0.4, # 政绩极佳 +40% 概率
            "patron_bonus": patron * 0.05,                  # 靠山说话 +N%
            "risk_penalty": -(risk / 100.0) * 0.3,          # 身上有雷 -30% 概率
            "competition_penalty": -0.1                     # 默认有强力竞争者
        }
        
        final_p = base_p + sum(modifiers.values())
        final_p = max(0.05, min(0.95, final_p))

        # --- 3. 掷骰子 ---
        rng = random.Random(seed)
        roll = rng.random()
        is_success = roll <= final_p

        audit = ProbabilityAudit(
            action_type="promotion_evaluation",
            base_probability=base_p,
            modifiers=modifiers,
            final_probability=final_p,
            roll_value=roll,
            is_success=is_success,
            rng_seed=seed
        )
        
        return is_success, audit