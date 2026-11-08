from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional
from datetime import datetime

class Attempt(BaseModel):
    """
    子动作尝试。
    玩家说“我暂缓签字并约老周吃饭”，会被 AI 解析成两个 Attempt。
    """
    attempt_id: str = Field(..., description="子动作的唯一ID")
    type: str = Field(..., description="动作类型，如 defer_signature, request_meeting, use_item")
    target_id: str = Field(..., description="动作的目标实体ID，如 doc_17, npc_zhou")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="动作附带的参数")
    time_hint: Optional[str] = Field(None, description="时间暗示，如 tonight, tomorrow")

class Command(BaseModel):
    """
    统一命令入口。
    无论是玩家、NPC 还是定时任务，都必须构造一个 Command 丢进系统。
    """
    command_id: str = Field(..., description="全局唯一的幂等键，防止重复提交")
    source: Literal["player", "npc", "system", "scheduler"] = Field(..., description="命令来源")
    actor_id: str = Field(..., description="执行该动作的实体ID")
    
    # 乐观锁：防止两个并发动作修改同一个状态
    expected_revision: int = Field(..., description="玩家提交此命令时，客户端持有的世界版本号")
    
    world_time: datetime = Field(..., description="提交此命令的游戏内时间")
    intent_text: Optional[str] = Field(None, description="玩家的原始自由文本，仅作日志保留")
    
    attempts: List[Attempt] = Field(default_factory=list, description="拆分后的子动作列表")
    
    # 理智确认机制（用于极端动作）
    is_high_risk_confirmed: bool = Field(False, description="如果是极端动作，玩家是否在UI上点击了'继续'")