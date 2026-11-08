from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class CommittedEvent(BaseModel):
    """
    已经发生的事实。
    一旦由 Committer 写入数据库，任何 AI、任何逻辑都不得修改它。
    """
    event_id: str = Field(..., description="事实的唯一ID")
    command_id: str = Field(..., description="溯源：由哪个命令触发的")
    
    sequence: int = Field(..., description="世界时间线内的绝对递增序号，用于保证因果顺序")
    world_time: datetime = Field(..., description="事件发生时的游戏内时间")
    
    actor_id: str = Field(..., description="谁做的")
    event_type: str = Field(..., description="事件类型，如 signature_deferred, npc_died, resource_stolen")
    
    # 核心载荷：这里存具体发生了什么。
    # 注意：这里存的内容就是“上帝视角的监控录像”。
    payload: Dict[str, Any] = Field(..., description="事件的具体内容和数据")
    
    # 因果链追溯（防止AI胡编乱造，必须有来源）
    caused_by: List[str] = Field(default_factory=list, description="是由哪些之前的事件导致的")
    
    # 审计信息
    rule_version: str = Field(..., description="裁定此事件时使用的规则版本")
    is_failure: bool = Field(False, description="如果这是一个失败的尝试（且被观察到了），也记作事件")