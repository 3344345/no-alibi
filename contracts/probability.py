from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ProbabilityAudit(BaseModel):
    """
    概率审计记录。
    不仅用于系统计算，更关键的是给开发者（World Inspector）回溯用。
    如果玩家觉得自己被针对了，你可以调出这条记录甩给他看。
    """
    action_type: str
    base_probability: float = Field(..., description="基础成功率")
    modifiers: Dict[str, float] = Field(default_factory=dict, description="各因素修正值")
    final_probability: float = Field(..., description="最终成功率")
    roll_value: float = Field(..., description="掷骰子结果（0.0 - 1.0）")
    is_success: bool = Field(..., description="是否成功")
    rng_seed: str = Field(..., description="使用的随机种子")