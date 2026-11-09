# content/projects.py

INITIAL_PROJECTS = {
    "proj_jinshan_road": {
        "name": "金山县环城公路",
        "description": "要想富先修路，但财政局连买沥青的钱都没有。",
        "manager": "npc_wangdalu",
        "real_progress": 0.1,      # 真实进度 10%
        "reported_progress": 0.1,  # 汇报进度 10%（还没开始造假）
        "budget": 100000,          # 当前只有10万
        "required_funds": 1000000, # 还需要90万
        "status": "stalled",
        "hidden_risk": "如果为了搞钱强制干部集资，会引发大规模上访。"
    },
    "proj_lead_mine": {
        "name": "金山县铅锌矿",
        "description": "县里唯一的利税大户，但污染严重。",
        "manager": "npc_yixuexi",
        "real_progress": 0.8,
        "reported_progress": 0.8,
        "budget": 500000,
        "status": "active",
        "hidden_risk": "环保督查组如果来了，矿必须停，县里财政彻底崩溃。"
    }
}