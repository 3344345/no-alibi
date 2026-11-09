from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Case(BaseModel):
    """
    长期发展的局势或危机（如工程进度失真、贪腐调查）。
    它会跨季度存在，并在特定时间点或条件满足时爆发。
    """
    case_id: str
    title: str
    description: str
    
    # 状态：latent(潜伏) -> signal(线索) -> contested(争议/处理中) -> active(爆发) -> resolved(解决)
    state: str = Field("latent")
    
    # 涉及的人物与项目
    involved_actors: List[str] = Field(default_factory=list)
    related_projects: List[str] = Field(default_factory=list)
    
    # 下一次检查时间（调度器用）
    next_check_time: Optional[datetime] = None
    
    # 历史关联
    root_event_id: str