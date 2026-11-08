class SystemException(Exception):
    """所有自定义异常的基类"""
    pass

class ConcurrencyError(SystemException):
    """乐观锁冲突：玩家提交命令时的世界版本，与当前数据库不一致"""
    pass

class ValidationError(SystemException):
    """Pydantic 数据校验失败"""
    pass
from enum import Enum

class ConstraintErrorCode(str, Enum):
    TARGET_NOT_FOUND = "TARGET_NOT_FOUND"       # 目标不存在
    OUT_OF_REACH = "OUT_OF_REACH"               # 距离不够/不在同一场景
    NO_AUTHORITY = "NO_AUTHORITY"               # 职级/权限不足
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"   # 资源不足（如钱、体力）
    MISSING_ITEM = "MISSING_ITEM"               # 物品不在身上（比如没带枪、没带记事本）
    INVALID_STATE = "INVALID_STATE"             # 目标状态不允许（如对死人问话）
    NO_PROCEDURE = "NO_PROCEDURE"               # 违反机构程序（如跳过审批直接拿钱）