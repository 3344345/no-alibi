from typing import Dict, Any, Optional
from pydantic import BaseModel
from contracts.command import Attempt
from contracts.errors import ConstraintErrorCode

class ConstraintResult(BaseModel):
    """硬约束校验的结果"""
    is_valid: bool
    error_code: Optional[ConstraintErrorCode] = None
    error_message: Optional[str] = None

class ConstraintValidator:
    """
    硬约束判定器（J2）。
    注意：这是一个纯函数模块，绝对不包含任何随机性（概率）、也不读写数据库。
    它只负责用无情的物理与制度规则，过滤掉不可能发生的动作。
    """
    
    @classmethod
    def validate(cls, attempt: Attempt, world_snapshot: Dict[str, Any]) -> ConstraintResult:
        """
        校验单个子动作是否合法。
        world_snapshot: 是传入的当前世界状态投影（只读），包含实体位置、玩家库存、职级等。
        """
        
        # 1. 存在性校验 (Target Exists)
        # 如果 attempt.target_id 不为空，检查目标是否存在于世界中
        if attempt.target_id:
            target = world_snapshot.get("entities", {}).get(attempt.target_id)
            if not target:
                return ConstraintResult(
                    is_valid=False, 
                    error_code=ConstraintErrorCode.TARGET_NOT_FOUND,
                    error_message=f"对象 {attempt.target_id} 不存在或不在可感知范围内。"
                )
            
            # 检查目标是否还活着/处于可用状态
            if target.get("status") in ["dead", "destroyed", "unreachable"]:
                 return ConstraintResult(
                    is_valid=False, 
                    error_code=ConstraintErrorCode.INVALID_STATE,
                    error_message=f"目标 {attempt.target_id} 当前状态无法执行此动作。"
                )

        # 2. 物理/空间校验 (Location & Reach)
        actor_id = world_snapshot.get("current_command_actor")
        actor_location = world_snapshot.get("actors", {}).get(actor_id, {}).get("location")
        target_location = target.get("location") if attempt.target_id else None
        
        # 如果动作需要接触（如递交文件、掏枪、吃饭），必须在同一场景
        if attempt.type in ["hand_over", "physical_attack", "use_item_on", "whisper_to"]:
            if actor_location != target_location:
                return ConstraintResult(
                    is_valid=False, 
                    error_code=ConstraintErrorCode.OUT_OF_REACH,
                    error_message="你们不在同一个空间，无法执行物理动作。"
                )

        # 3. 库存校验 (Inventory & Items)
        # 比如玩家没带枪，就不能“掏枪”；没带记事本，就不能“在上面写字”。
        if attempt.type == "draw_weapon":
            actor_inventory = world_snapshot.get("actors", {}).get(actor_id, {}).get("inventory", [])
            if "item_gun" not in actor_inventory:
                return ConstraintResult(
                    is_valid=False, 
                    error_code=ConstraintErrorCode.MISSING_ITEM,
                    error_message="你摸向腰间，但发现自己今天没有配枪。"
                )
                
        # 4. 权限与职级校验 (Authority & Rank)
        # 如果动作是强制命令，检查职级压制
        if attempt.type in ["command", "demand_resource", "fire_employee"]:
            actor_rank = world_snapshot.get("actors", {}).get(actor_id, {}).get("rank", 0)
            target_rank = target.get("rank", 0) if target else 0
            
            if actor_rank < target_rank:
                return ConstraintResult(
                    is_valid=False, 
                    error_code=ConstraintErrorCode.NO_AUTHORITY,
                    error_message="你的行政级别不足以直接对该目标下达强制指令。"
                )
                
        # 5. 资源校验 (Resources)
        # 比如要求财政部门拨款，实际上财政局账上没钱
        if attempt.type == "request_funds":
            amount = attempt.parameters.get("amount", 0)
            treasury_balance = world_snapshot.get("institutions", {}).get("treasury", {}).get("balance", 0)
            if treasury_balance < amount:
                return ConstraintResult(
                    is_valid=False, 
                    error_code=ConstraintErrorCode.RESOURCE_EXHAUSTED,
                    error_message="财政账面上没有这么多可调拨资金。"
                )

        # 如果所有硬条件都通过，返回合法
        return ConstraintResult(is_valid=True)