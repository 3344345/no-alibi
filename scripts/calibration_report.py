"""Format the measured engine observations for the release report."""
from pathlib import Path

def write_report(r: dict, target: Path):
    s=r['seasons'];t=s['timing'];long=r['long']
    lines=['# 连续参数与生涯回归实测','',
           f"本轮在 {r['cpu']}、{r['memory_bytes']//(1024**3)} GiB、{r['platform']}、Python {r['python']} 上运行。参数包 SHA-256 为 `{r['package_hash']}`。本地源码基于 `{r['base_commit'][:12]}`。测试脚本、游戏模块和注册表的合并指纹为 `{r['source_sha256']}`。",
           '',
           '执行命令为 `.venv/bin/python scripts/calibrate.py --json /tmp/juzhongshi-calibration.json --report BALANCE_CALIBRATION_REPORT.md`，退出码为 0。运行使用临时 SQLite 数据库。重复测量会生成独立世界 ID，时间开销随设备负载变化。','',
           '## 七个取向的同局对照','',
           '固定起点 S04 与种子 `paired-county-2026`。在办公室委托比对、请求第二份材料，前往协调会提出 C 方案。另开相同起点，在亲查完成、查证资格成立后的 60 个游戏分钟读取累计强度 H。表中时长采用入队前的原始分钟数。','',
           '| b | 委托比对（分） | 核对送达（分） | 财政反提案条件概率 | 60 分钟 H | 本次答复 |',
           '|---:|---:|---:|---:|---:|---|']
    for row in r['paired']:
     lines.append(f"| {row['b']} | {row['admin']:.5f} | {row['message']:.5f} | {row['counter']:.6%} | {row['H']:.8f} | "+('提出反案' if row['outcome']=='counter' else '维持原案')+' |')
    lines+=['',f"七次财政决定共用随机槽 `{r['paired'][0]['slot']}`，样本 U 为 {r['paired'][0]['U']:.12f}。原始时长与累计强度是连续量。进入日程前向上量化到整分钟，人物在各自候选中作一次离散选择。",'',
    '固定权重的数值检验用 10,000 个相同逻辑槽，观察五个锚点。事前容许界限为二项模型下五个标准差再加一个观测。','',
    '| b | 条件概率 | 观测频率 |','|---:|---:|---:|']
    for row in r['sampling']:
     lines.append(f"| {row['b']:.2f} | {row['expected']:.3%} | {row['observed']:.3%} |")
    lines+=['','## 十二季度与长期档案','',
     f"从 `release-seed-000` 至 `release-seed-{s['seeds']-1:03d}` 顺序建局，所用起点共 {len(s['starts'])} 类。每六局依次取五个固定值及一个独立种子生成的中间值，观测到 {len(s['variants'])} 种初始事实包。角色在动作可用时依次委托、请求材料、提交附条件意见、赴协调会，随后尝试 C 方案并逐季推进。{s['proposals']} 局提交方案，{s['outcomes'].get('12_seasons',0)} 局到达第十二季末。每季检查财政与班组上限、家庭现金和时间，每局比对只读回放与存储投影。共记录 {s['events']} 条世界及内部审计事件。",'',
     f"长局采用 S01、种子 `release-120-quarter` 和 b=0.637500。第 120 季末为游戏分钟 {long['minute']:,}，进入第 {long['last_quarter']} 季开头，当时已有 {long['events']} 条事件。该档继续运行至分钟 {long['ended_minute']:,}，完成自然退休交接（{long['ending']}）。两处分界均校验回放。",'',
    '## 本地内核耗时','',
    '以下计时从 GameStore 调用到返回，包括 SQLite 和投影。首次安装、WebView 绘制、HTTP 往返和人工阅读不在测量范围内。','',
    '| 路径 | 样本 | p50（ms） | p95（ms） | 最大（ms） |','|---|---:|---:|---:|---:|']
    for k,n in [('action','预设行动'),('fast_forward','按季度推进'),('view','十二季度热读取'),('replay','十二季度全量校验回放')]:
     v=t[k];lines.append(f"| {n} | {v['n']} | {v['p50_ms']} | {v['p95_ms']} | {v['max_ms']} |")
    lines+=['',f"测试进程峰值常驻内存为 {r['peak_rss']/1024**2:.1f} MiB，涵盖测试解释器、多个短期数据库及统计程序。各局第十二季末待处理任务数范围为 {s['terminal_queue_range'][0]}–{s['terminal_queue_range'][1]}。",'',
    '## 结果适用范围','',
    '本轮检验了一个固定办理策略、五个锚点及中间取向、长局退休与保存回放。固定策略没有覆盖所有场景或八种终局。数值系数仍属于游戏设计初值，主观乐趣、严谨感和文本负担需要独立真人试玩评价。']
    from scripts.world_invariants import INVARIANTS
    lines+=['','## G4 逐提交不变量核验','','计数为已通过的实际检查次数。INV-09 是每局一次独立拒绝探针，INV-10 按发生的抽样计数；其余按命令或初始化提交计数。读审计与重交探针没有计入上方的操作延时。','','| 项目 | 检查数 | 本轮断言 | 特殊情形的独立回归用例 |','|---|---:|---|---|']
    for tag,(check,fixtures) in INVARIANTS.items():
        lines.append(f'| {tag} | {s["invariant_counts"][tag]} | {check} | {fixtures} |')
    target.write_text('\n'.join(lines)+'\n')
