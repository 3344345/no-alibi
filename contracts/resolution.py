from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional
from contracts.event import CommittedEvent

class AttemptResult(BaseModel):
    """针对单个子动作的裁定结果"""
    attempt_id: str
    status: Literal["success", "failed", "partial_success", "pending", "invalid", "cancelled"] = Field(..., description="动作结局")
    reason_code: Optional[str] = Field(None, description="如果失败或被拒，原因码是什么")
    description: str = Field(..., description="底层系统对结果的机械描述（非给玩家看的AI文案）")

class Resolution(BaseModel):
    """
    Resolver 的产出。
    它包含了结果判定，但还没有写入数据库。等待 Committer 原子化提交。
    """
    command_id: str
    attempt_results: List[AttemptResult]
    
    # 需要 Committer 写入数据库的新事件
    generated_events: List[CommittedEvent] = Field(default_factory=list)
    
    # 副作用（如扣钱、改变人物好感），交由 Committer 更新 Projection
    state_changes: Dict[str, Any] = Field(default_factory=dict, description="需要应用到世界状态的具体数值修改")
    
    # 需要传播的信息（如老周看到了这一幕）
    pending_observations: List[Dict[str, Any]] = Field(default_factory=list, description="待传播的消息/观察记录")