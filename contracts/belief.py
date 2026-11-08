from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class Message(BaseModel):
    """
    消息载体。
    比如：老周递交了一份报告，报告上写着“工程正常”。
    注意：claim（声称的内容）只是载体，绝不等于世界事实。
    """
    message_id: str
    sender_id: str = Field(..., description="发送者，如 npc_zhou")
    channel: str = Field(..., description="传播渠道，如 document_briefing, whisper, phone_call")
    claim: str = Field(..., description="声称的具体内容（可能是谎言，可能是事实）")
    related_event_ids: List[str] = Field(default_factory=list, description="底层关联了什么真实事件")
    confidentiality_scope: str = Field("public", description="机密级别，决定谁能看到")

class Observation(BaseModel):
    """
    观察记录。
    接收者确实看到了/听到了这条消息。
    """
    observation_id: str
    recipient_id: str = Field(..., description="接收者，如 player, npc_li")
    message_id: str
    delivered_at: datetime
    
class Belief(BaseModel):
    """
    NPC 或玩家最终形成的认知。
    这是 AI 扮演该角色时，唯一能读取的上下文。
    """
    belief_id: str
    owner_id: str
    claim: str = Field(..., description="他脑子里相信的内容")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="他有多确信（0-1）")
    based_on_observation_ids: List[str] = Field(..., description="因为看到了哪些观察记录才信的")
    is_true: bool = Field(False, description="这是上帝视角：他信的东西到底是不是真的")