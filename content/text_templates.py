# content/text_templates.py

# 动作成功的通用叙事
SUCCESS_TEMPLATES = {
    "default": "你的指令传达了下去，下面的人大概是开始按你的意思行动了。",
    "defer_signature": "你合上了文件夹，没有签字。秘书识趣地把文件拿走了，你知道这事拖不了太久。",
    "request_meeting": "你让人安排了会面，对方答应得很快，但你不知道他是不是真的做好了准备。"
}

# 动作失败的通用叙事
FAILURE_TEMPLATES = {
    "default": "事情没有按你预想的发展，中间出了岔子。",
    "NO_AUTHORITY": "对方虽然表面上客客气气，但话里话外都在拿级别压你。你碰了个软钉子。",
    "MISSING_ITEM": "你摸向口袋，发现自己根本没带那件东西。"
}

# 晋升相关的叙事
PROMOTION_TEMPLATES = {
    "promotion_success": "市委组织部找你谈了话。几天后，调令下来了，你被提拔了。周围的人看你的眼神都不一样了。",
    "promotion_failed": "你听说那个空缺的位置被隔壁县的人拿走了。市委领导说：“达康同志，不要有情绪，组织上对你有更重要的安排。”"
}

# 系统调度/NPC主动行动
SYSTEM_TEMPLATES = {
    "npc_wakeup": "门外传来了急促的脚步声。你的门被推开，是老周。他的脸色苍白，似乎一宿没睡。",
    "case_trigger": "工程队的人堵在了县政府门口。领头的工头大声喊着，说今天再拿不到材料款，谁也别想开工。"
}

def get_narrative_by_event_type(event_type: str, is_failure: bool = False) -> str:
    """简单的查表逻辑，供离线 Narrator 使用"""
    if is_failure:
        return FAILURE_TEMPLATES.get(event_type, FAILURE_TEMPLATES["default"])
    
    if event_type in SUCCESS_TEMPLATES:
        return SUCCESS_TEMPLATES[event_type]
    if event_type in PROMOTION_TEMPLATES:
        return PROMOTION_TEMPLATES[event_type]
    if event_type in SYSTEM_TEMPLATES:
        return SYSTEM_TEMPLATES[event_type]
        
    return SUCCESS_TEMPLATES["default"]