# content/characters.py

INITIAL_ACTORS = {
    "player": {
        "name": "李达康",
        "role": "金山县县长",
        "rank": 4, # 正处级
        "location": "jinshan_office",
        "inventory": ["item_notebook", "item_pen", "cigarette_pack"],
        "mental_state": "focused", 
        
        # --- 供 J7 晋升引擎读取的核心属性 ---
        "age": 35,
        "tenure_years": 4,
        "performance_score": 85, 
        "patron_influence": 3, # 秘书帮背景
        "hidden_risk": 10, # 目前身上没大雷
        
        "goals": ["修通金山县的路", "拿到市委的财政支持", "防范易学习的连带风险"]
    },
    "npc_yixuexi": {
        "name": "易学习",
        "role": "金山县县委书记",
        "rank": 5, # 正处级，李达康的直接搭班子同事
        "location": "jinshan_office",
        "mental_state": "normal",
        "goals": ["求稳", "保证县里不出乱子"],
        "beliefs": {"player_is_too_radical": True}
    },
    "npc_wangdalu": {
        "name": "王大路",
        "role": "金山县城投公司经理",
        "rank": 3, 
        "location": "construction_site",
        "mental_state": "terrified", # 极度缺钱，随时可能爆雷，会主动找玩家
        "goals": ["搞到修路的钱", "替李达康背锅"],
        "beliefs": {"must_protect_li_dakang": True}
    },
    "npc_zhao": {
        "name": "赵瑞龙",
        "role": "省委书记之子 / 商人",
        "rank": 0, 
        "location": "outside",
        "mental_state": "greedy",
        "goals": ["空手套白狼", "在金山县拿地"],
        "beliefs": {"all_officials_can_be_bought": True}
    }
}