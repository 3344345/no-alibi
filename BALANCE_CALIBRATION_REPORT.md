# 连续参数与生涯回归实测

本轮在 Apple M5 Max、128 GiB、macOS-27.2-arm64-arm-64bit、Python 3.12.15 上运行。参数包 SHA-256 为 `241cc2ea2ba1bee4505a791fc415ee9c33ec7a496bab461d9a8b514af48a73dc`。本地源码基于 `75d9559c12cc`。测试脚本、游戏模块和注册表的合并指纹为 `e11f6f93773174167310f17f110a384968d817403d7097904120944175fe7694`。

执行命令为 `.venv/bin/python scripts/calibrate.py --json /tmp/juzhongshi-calibration.json --report BALANCE_CALIBRATION_REPORT.md`，退出码为 0。运行使用临时 SQLite 数据库。重复测量会生成独立世界 ID，时间开销随设备负载变化。

## 七个取向的同局对照

固定起点 S04 与种子 `paired-county-2026`。在办公室委托比对、请求第二份材料，前往协调会提出 C 方案。另开相同起点，在亲查完成、查证资格成立后的 60 个游戏分钟读取累计强度 H。表中时长采用入队前的原始分钟数。

| b | 委托比对（分） | 核对送达（分） | 财政反提案条件概率 | 60 分钟 H | 本次答复 |
|---:|---:|---:|---:|---:|---|
| 0.000000 | 75.00000 | 100.00000 | 35.000000% | 0.02083333 | 提出反案 |
| 0.250000 | 67.68750 | 90.37500 | 40.372536% | 0.02500000 | 提出反案 |
| 0.499000 | 60.40425 | 80.78850 | 45.963550% | 0.02915000 | 提出反案 |
| 0.500000 | 60.37500 | 80.75000 | 45.986309% | 0.02916667 | 提出反案 |
| 0.501000 | 60.34575 | 80.71150 | 46.009069% | 0.02918333 | 提出反案 |
| 0.750000 | 53.06250 | 71.12500 | 51.703811% | 0.03333333 | 提出反案 |
| 1.000000 | 45.75000 | 61.50000 | 57.377049% | 0.03750000 | 提出反案 |

七次财政决定共用随机槽 `fiscal/conditions/40778e8a3229c6128db2a9ce16ecbe55bcad5f10ab5d3a8b92b75a8b1337d2c2`，样本 U 为 0.097638099463。原始时长与累计强度是连续量。进入日程前向上量化到整分钟，人物在各自候选中作一次离散选择。

固定权重的数值检验用 10,000 个相同逻辑槽，观察五个锚点。事前容许界限为二项模型下五个标准差再加一个观测。

| b | 条件概率 | 观测频率 |
|---:|---:|---:|
| 0.00 | 35.000% | 35.660% |
| 0.25 | 40.373% | 41.030% |
| 0.50 | 45.986% | 46.420% |
| 0.75 | 51.704% | 51.980% |
| 1.00 | 57.377% | 57.330% |

## 十二季度与长期档案

从 `release-seed-000` 至 `release-seed-099` 顺序建局，所用起点共 8 类。每六局依次取五个固定值及一个独立种子生成的中间值，观测到 4 种初始事实包。角色在动作可用时依次委托、请求材料、提交附条件意见、赴协调会，随后尝试 C 方案并逐季推进。100 局提交方案，100 局到达第十二季末。每季检查财政与班组上限、家庭现金和时间，每局比对只读回放与存储投影。共记录 14492 条世界及内部审计事件。

长局采用 S01、种子 `release-120-quarter` 和 b=0.637500。第 120 季末为游戏分钟 15,552,000，进入第 121 季开头，当时已有 1066 条事件。该档继续运行至分钟 16,588,920，完成自然退休交接（END01）。两处分界均校验回放。

## 本地内核耗时

以下计时从 GameStore 调用到返回，包括 SQLite 和投影。首次安装、WebView 绘制、HTTP 往返和人工阅读不在测量范围内。

| 路径 | 样本 | p50（ms） | p95（ms） | 最大（ms） |
|---|---:|---:|---:|---:|
| 预设行动 | 400 | 2.48 | 2.92 | 5.08 |
| 按季度推进 | 1200 | 3.05 | 3.7 | 6.94 |
| 十二季度热读取 | 100 | 1.22 | 1.4 | 4.14 |
| 十二季度全量校验回放 | 100 | 13.41 | 16.48 | 20.74 |

测试进程峰值常驻内存为 58.3 MiB，涵盖测试解释器、多个短期数据库及统计程序。各局第十二季末待处理任务数范围为 2–3。

## 结果适用范围

本轮检验了一个固定办理策略、五个锚点及中间取向、长局退休与保存回放。固定策略没有覆盖所有场景或八种终局。数值系数仍属于游戏设计初值，主观乐趣、严谨感和文本负担需要独立真人试玩评价。

## G4 逐提交不变量核验

计数为已通过的实际检查次数。INV-09 是每局一次独立拒绝探针，INV-10 按发生的抽样计数；其余按命令或初始化提交计数。读审计与重交探针没有计入上方的操作延时。

| 项目 | 检查数 | 本轮断言 | 特殊情形的独立回归用例 |
|---|---:|---|---|
| INV-01 | 1900 | 每次命令的收据、日志和状态哈希一致 | test_disk_full_rolls_back_and_backup_replace_is_atomic；test_bounded_advisor_transport_and_fallback |
| INV-02 | 1900 | 日志连续、哈希前驱一致，事件 ID 和分钟有序 | test_integrity_branch_replay_and_wal_backup |
| INV-03 | 1800 | 逐命令原请求重交，验证返回相同且写入数不变 | test_v4_t17_atomicity_concurrency_idempotence |
| INV-04 | 1900 | 每个信念引用该角色先验或已提交事件 | test_invitation_refusal_and_actual_arrival_have_separate_witnesses；test_sourced_notes_arrive_in_custody_then_receive_partial_corroboration |
| INV-05 | 1900 | PlayerView 键和时间线均通过可见性检查，失去本子时无原文 | test_bounded_advisor_transport_and_fallback；test_notebook_private_and_clocked_exposure |
| INV-06 | 1900 | 时钟单调、队列不残留过期任务，已提交事件不早于前一版本 | test_v4_t19_t22_opportunity_and_pause |
| INV-07 | 1900 | 年度和季度额度、预留、工作组、薪酬和物品来源有效 | test_conditional_budget_and_real_work；test_role_grant_lease_and_reject_forgery |
| INV-08 | 1900 | 实际案卷、材料、岗位认定与终局引用属于已提交事件 | test_acquired_evidence_and_formal_ending；test_all_cases_can_receive_new_material_after_three_quarters |
| INV-09 | 100 | 无权开放的请求遭拒，验证三张表没有副作用 | test_conditional_budget_and_real_work；test_role_grant_lease_and_reject_forgery |
| INV-10 | 200 | 实际抽样槽、样本、权重、规则包及封存结果可复算 | test_integrity_branch_replay_and_wal_backup；test_same_minute_policy_changes_keep_thresholds_and_existing_tasks |
| INV-11 | 1900 | 无检查和授权的开放无法提交；已开放设施均有批准 | test_service_and_accessible_evidence_with_divergent_paths；test_late_career_retirement_care_and_health_records |
| INV-12 | 1900 | 核对待处理任务的唯一 ID、派生根、同分钟深度和有界扇出 | test_scheduler_contains_same_minute_cycles_and_keeps_task |
