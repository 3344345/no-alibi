# content/cases.py

from datetime import datetime
from domain.case import Case

# 注意：实际游戏中，时间的初始化应该是相对于当前游戏时间。
# 这里为了演示，生成一个在 1991年6月1日 触发的危机
INITIAL_CASES = [
    Case(
        case_id="case_road_fund",
        title="修路资金链断裂危机",
        description="城投公司拿不出钱，工程队准备罢工。",
        state="latent",
        involved_actors=["player", "npc_wangdalu"],
        related_projects=["proj_jinshan_road"],
        next_check_time=datetime(1991, 6, 1, 10, 0, 0), # 1991年6月1日 触发
        root_event_id="evt_init_001"
    )
]