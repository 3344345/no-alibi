# 《局中事》验收记录

本次以 V4.0 第 12–13 章为连续参数和发布依据，继承 S30 第 14–15 章与 S31 第 46 页的原编号。能够在本机运行的功能候选已完成多层验证。对原始夹具的专用断言、跨版本档案、真实模型及真人试验仍需独立证据。

## 如何复核

- [需求证据矩阵](REQUIREMENTS_TRACEABILITY.csv) 保留 423 条内嵌历史来源。每行含原 ID、原文件、原页、条文、当前对应门槛、实现位置和可运行命令。来源中的封面、风险登记、开发建议和延期范围不作为软件通过项。标为“原条款待逐项核对”的行只建立了关联入口。
- 在仓库根运行 `.venv/bin/python -m pytest --disable-warnings -q`。本轮截取时实际退出码为 0，共 132 项通过，另有一条上游测试客户端弃用提示。表内源码测试链接可直接定位断言。CSV 的命令列提供可单独执行的 pytest 节点。
- 运行 `.venv/bin/python scripts/calibrate.py --json /tmp/jzs-calibration.json --report BALANCE_CALIBRATION_REPORT.md` 复核 100 种子、12 季、120 季、配对数值与模拟不变量。系统及代码指纹、各条件的观测与范围见[实测报告](BALANCE_CALIBRATION_REPORT.md)。
- `cd frontend && npm run test:e2e` 运行浏览器旅程。桌面真机、同机升级/恢复、实际联网提供方与真人体验由独立记录判定。

“已实测”表示行内所述条件已有实际断言或观测。“部分”列出尚缺的原场景、统计边界或验证层。“待测”保留有明确通过标准而未取得证据的条款。相同测试可支撑多个来源编号，门槛不能按测试总数推算。

## 外部与兼容边界

- V3.0/V3.1 正式游戏存档原件尚未提供。本产品 SQLite 旧结构、坏/缺快照、原型识别及备份恢复已有实际检查。[兼容范围](SAVE_COMPATIBILITY.md)
- 数学、代理回归和本机模型替身提供各自的运行证据。六位真实参与者的轮换任务、观察与反馈须随建版独立记录。[真人试玩记录](PLAYTEST_REPORT.md)

## 放行门槛

| 编号 | 要求 | 状态 | 运行证据及边界 |
|---|---|---|---|
| G0 | 契约冻结与来源映射 | 部分 | 连续参数和事件合同已检查。全领域类型和八个原始夹具仍有缺项。 [register_matches_world_and_all_32_mechanisms](tests/test_world_v4.py#L315) |
| G1 | 提交、持久化、重放与恢复 | 部分 | 实际五个事务写点、并发/重试、只读回放和通知租约恢复均已验证；原全量对象/独立消息任务归一化约束仍见 G0。 [every_sql_write_position_rolls_back](tests/test_delivery_recovery.py#L69) |
| G2 | J1–J9 判定 | 部分 | 批处理依赖、预算、人物选择、人事、调查和终局样例经测试。通用确认及被目击的失败仍缺独立回归。 [batch_partial_execution_and_causal_dependency](tests/test_player_api.py#L158) |
| G3 | E1–E10 事件 | 部分 | 定时、传播、Case 与同分钟隔离有实测。原版独立 Outbox 租约与完整订阅合同仍有差异。 [scheduler_contains_same_minute_cycles_and_keeps_task](tests/test_player_api.py#L127) |
| G4 | 互操作与 100 种子十二季 | 已实测 | 原 C01–C10 已有完整来源路径或专门接口试验。100 局十二季逐步执行十二类不变量检查，120 季观察单列数值报告。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| G5 | 四类 AI 角色与离线降级 | 部分 | 本机 HTTP 假服务实际检查越权候选与回退。真实付费模型另列放行证据。 [bounded_advisor_transport_and_fallback](tests/test_player_api.py#L75) |
| G6 | 普通玩家界面完整旅程 | 部分 | 浏览器脚本覆盖办事、存档、资料台与多个起点。原多季、多人、多个场景组合旅程需逐项核对。 [浏览器旅程](frontend/tests/browser.test.mjs) |
| G7 | 硬化、迁移、原测试与发布条件 | 部分 | 当前格式与回放经实测；缺真实 V3 迁移、部分旧夹具和完整发布证据。 [integrity_branch_replay_and_wal_backup](tests/test_engine_v4.py#L287) |
| G8 | 全部世界内容与交互边界 | 部分 | 数量、10 场景多路线、六弧线、16 跨季案、八起点/终局和 32 机制正反例已有可重现证据。全部实体替换/八起点×八结局的完整矩阵仍需复核。 [register_matches_world_and_all_32_mechanisms](tests/test_world_v4.py#L315) |
| G9 | 本机发行、分发与反馈 | 部分 | 桌面和真人证据由相应验证记录单列，六名真人试验未在数值回归中进行。 [macOS 构建](scripts/build_macos.sh) |

## 连续参数计算与接入

| 编号 | 要求 | 状态 | 运行证据及边界 |
|---|---|---|---|
| V4-T01 | 端点与 1001 点 | 已实测 | 逐点检查系数、目标权重及邻点变化。 [v4_t01_t03_1001_points_and_neighbours](tests/test_engine_v4.py#L22) |
| V4-T02 | 六位规范十进制输入 | 已实测 | 布尔、空白、非法小数、超界和非有限值请求均受校验。 [v4_t02_strict_target](tests/test_engine_v4.py#L54) |
| V4-T03 | 相邻值与随机邻域 | 已实测 | 512 个确定性随机邻域逐一检查有符号差商，包括线性系数、指数权重和目标分配。 [v4_t03_paired_random_neighbourhood_gradients](tests/test_balance_crosscuts.py#L22) |
| V4-T04 | 含 none 的稳定软最大 | 已实测 | 黄金向量、无 none、零分数、稳定候选排序有检查。 [v4_t04_t05_t08_official_golden](tests/test_engine_v4.py#L66) |
| V4-T05 | 整数分钟与营业日历 | 已实测 | 独立基准对齐原始/进位时长，跨周末有执行边界。 [v4_t04_t05_t08_official_golden](tests/test_engine_v4.py#L66) |
| V4-T06 | 240 分钟过渡与中途转向 | 已实测 | 标准点与独立积分已查。控制重启见同文件 committed_policy_and_resume。 [v4_t06_t07_ramp_quadrature](tests/test_engine_v4.py#L102) |
| V4-T07 | 累计强度积分 | 已实测 | 分段相加、静态与独立细步积分对照，并由机会时钟测试检查切片。 [v4_t06_t07_ramp_quadrature](tests/test_engine_v4.py#L102) |
| V4-T08 | 反提案边界 | 已实测 | P0 等于 0 和 1 保持不变，五点中间概率与参考向量一致。 [v4_t04_t05_t08_official_golden](tests/test_engine_v4.py#L66) |
| V4-T09 | 实际办理、消息、反提案、机会四类中间量 | 已实测 | 相同种子七个取向经真实命令读取四种中间量，详见数值报告。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| V4-T10 | 各参数在注册环节只消费一次 | 已实测 | 同渠道的玩家请求与 NPC 寄送各留下一个成本绑定。其余路径的审计抽样见 paired。 [v4_t10_t14_npc_mail_shares_channel_receipt_gates_belief](tests/test_inspector.py#L12) |
| V4-T11 | 零 I/O 纯 Resolver | 已实测 | 相同快照执行真实跨季 Resolver 两次，守卫禁止文件/数据库/网络、系统钟、外部进程与随机熵，并逐项比较状态和事件。 [v4_t11_resolver_tape_is_pure_under_io_clock_and_entropy_guards](tests/test_balance_crosscuts.py#L38) |
| V4-T12 | 各取向的权限、物品、预算与物理前提 | 已实测 | 五个锚点各自测试无权签署、缺开放前置、无通行权、异地缺本、同池预算、班组与重复分配，拒绝前后状态一致。 [v4_t12_t26_authority_inventory_location_and_shared_budget](tests/test_balance_crosscuts.py#L64) |
| V4-T13 | 配置不改创世真相和已知范围 | 已实测 | 四变体经改设置后仍保持原初事实，独立材料通过真实渠道取得。 [all_four_frozen_explanations_and_repair](tests/test_world_v4.py#L77) |
| V4-T14 | 玩家与 NPC 同一过程 | 已实测 | 实际医院提案与玩家提案均送交同一财政负责人，五个锚点比较候选权重与绑定。真实回函改变医院准备计划，回复本身不拨款。 [v4_t14_same_finance_responder_real_npc_and_player_proposals](tests/test_balance_crosscuts.py#L96) |
| V4-T15 | 无资格不强派世界机会 | 已实测 | 五个取向各跨四季，关闭三个渠道的实际资格，不会为了剧情触发，H、episode、due 保持对应静止状态。 [v4_t15_disabled_eligible_processes_never_spawn_for_quota](tests/test_balance_crosscuts.py#L114) |
| V4-T16 | 控制日志与普通视图分离 | 已实测 | 控制事件在存档内可追溯，在角色时间线中不可见。 [v4_t16_t18_t20_t21_t23_committed_policy_and_resume](tests/test_engine_v4.py#L180) |
| V4-T17 | 并发、重试和事务回滚 | 已实测 | 同 ID 同请求命中原回执，不同请求拒绝；并发写冲突回滚。 [v4_t17_atomicity_concurrency_idempotence](tests/test_engine_v4.py#L217) |
| V4-T18 | 已封存任务维持绑定 | 已实测 | 多次改目标后检查队列、时间和费用快照逐项相同。 [same_minute_policy_changes_keep_thresholds_and_existing_tasks](tests/test_engine_v4.py#L384) |
| V4-T19 | 过期预测代际与重复触发 | 已实测 | 过期 generation 不触发；大步与细步的事件次数和时钟状态一致。 [v4_t19_t22_opportunity_and_pause](tests/test_engine_v4.py#L255) |
| V4-T20 | 同刻多次调参防重掷 | 已实测 | 四次确认不推进时间，保留原阈值、累计量与槽。 [same_minute_policy_changes_keep_thresholds_and_existing_tasks](tests/test_engine_v4.py#L384) |
| V4-T21 | 过期预览与确认 | 已实测 | 高影响命令验证与当前世界版本、动作和实参绑定的 HMAC；过期或篡改请求无法执行。 [confirmation_binds_terms_revision_and_receipt](tests/test_player_api.py#L200) |
| V4-T22 | 大步与细步推进 | 已实测 | 10000 分钟一次或 20×500 分钟后时钟完整状态逐项相同。 [v4_t19_t22_opportunity_and_pause](tests/test_engine_v4.py#L255) |
| V4-T23 | 过渡内重启与未完成任务 | 已实测 | 导出再恢复到另一个数据库后，继续命令与原局一致。 [v4_t16_t18_t20_t21_t23_committed_policy_and_resume](tests/test_engine_v4.py#L180) |
| V4-T24 | 旧档迁移与旧历史回放 | 部分 | 新格式可回放；原型识别和原件保护已测，V3 实档迁移尚待样本。 [unsupported_legacy_database_is_untouched](tests/test_engine_v4.py#L373) |
| V4-T25 | 八种开场及功能段交付 | 已实测 | 八起点首个履职动作另见 test_start_only_sees_own_prior_and_can_do_own_job；通路实测含缺条件拒绝。 [service_and_accessible_evidence_with_divergent_paths](tests/test_world_v4.py#L59) |
| V4-T26 | 三项目同池稀缺 | 已实测 | 五个锚点各自测试无权签署、缺开放前置、无通行权、异地缺本、同池预算、班组与重复分配，拒绝前后状态一致。 [v4_t12_t26_authority_inventory_location_and_shared_budget](tests/test_balance_crosscuts.py#L64) |
| V4-T27 | 四类初始事实包 | 已实测 | 四个解释持久化，核查获得的材料对应创世状态。 [all_four_frozen_explanations_and_repair](tests/test_world_v4.py#L77) |
| V4-T28 | 临时分析与实体记事本 | 已实测 | 未持原件无法读取全文，毁本后副本与来源仍在；临时草稿界面另有浏览器验证。 [notebook_private_and_clocked_exposure](tests/test_world_v4.py#L129) |
| V4-T29 | 十强化场景与六人物线 | 已实测 | 十个 SC 的区别路线和前置反例见 tests/test_scenario_routes_v4.py；本行测试另验证六线中间状态、来源与自主结局。 [six_character_arcs_have_sourced_intermediate_steps_and_branching_outcomes](tests/test_world_v4.py#L377) |
| V4-T30 | 可解释的不利后果、补救与合法终局 | 已实测 | 正式听证和交接走普通动作。另见同文件退休、恢复、边缘化及非调查终局。 [acquired_evidence_and_formal_ending](tests/test_world_v4.py#L177) |
| V4-T31 | 无网核心与在线降级 | 已实测 | 阻断 socket 外连，五个锚点真实走遍九地点、三项目验收开放、导师、实体本、12 季、主动离开及异库恢复。配置不可达提供方的配对世界与离线世界逐步相同。 [v4_t31_all_scenes_projects_mentors_and_ending_with_network_blocked](tests/test_balance_crosscuts.py#L167) |
| V4-T32 | 无信息反推捷径 | 已实测 | 四种真相包与五取向交叉，在已获资料相同条件下替换隐藏完成量、谜底与健康状态，比较全角色菜单、普通视图、机会资格、负荷及短期到达。 [v4_t32_hidden_ground_truth_cannot_change_visible_actions_or_advisor_input](tests/test_balance_crosscuts.py#L129) |

## 原判定与事件测试

| 编号 | 要求 | 状态 | 运行证据及边界 |
|---|---|---|---|
| T01 | 复合意图与部分完成 | 已实测 | 结构化 DAG 允许部分完成，独立子动作可继续；浏览器另测自由输入拆分。 [batch_partial_execution_and_causal_dependency](tests/test_player_api.py#L158) |
| T02 | 缺少持有物时不能凭空成功 | 已实测 | 实际玩家接口覆盖无物品的确认、取消和拒绝后的有限在场观察，禁止补造物品或无源后果。 [explicit_high_risk_intent_absent_item_and_limited_witnesses](tests/test_player_api.py#L230) |
| T03 | 预算不双花 | 已实测 | 两个部门在同一游戏分钟提交请求，争用同一额度及班组。未获全部资源的一方实际修改安排。 [c03_f04_independent_same_minute_department_claims_and_replan](tests/test_cross_system_routes.py#L105) |
| T04 | 无玩家派令仍有 NPC 行动 | 已实测 | 推进至自主寄件后实际产生待送任务，随后改变指定接收者认知。 [v4_t10_t14_npc_mail_shares_channel_receipt_gates_belief](tests/test_inspector.py#L12) |
| T05 | 按本人认知决策 | 已实测 | 所有正式 NPC 的实际候选输入在未知真相变化之后保持相同；送达合法来源产生变化的正例见投递测试。 [v4_t32_hidden_ground_truth_cannot_change_visible_actions_or_advisor_input](tests/test_balance_crosscuts.py#L129) |
| T06 | 随机与版本可复核 | 已实测 | 同槽 U 在七种政策保持一致，可由结果与版本校验。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| T07 | 看见被拒的尝试可以留痕 | 已实测 | 实际玩家接口覆盖无物品的确认、取消和拒绝后的有限在场观察，禁止补造物品或无源后果。 [explicit_high_risk_intent_absent_item_and_limited_witnesses](tests/test_player_api.py#L230) |
| T08 | 晋升的资格、空缺与程序 | 已实测 | 普通起点的跨岗位考察、材料和空缺链可达。 [cooperation_materials_sustain_a_complete_position_chain](tests/test_world_v4.py#L256) |
| T09 | 指控与事实分离 | 已实测 | 礼盒接触产生文书，单有接触未自动立案，后续凭实际取得及程序认定。 [acquired_evidence_and_formal_ending](tests/test_world_v4.py#L177) |
| T10 | 终局与职责合法转换 | 已实测 | 另有调查、主动退出、边缘化等正式旅程测试。 [late_career_retirement_care_and_health_records](tests/test_world_v4.py#L207) |
| T11 | 未知事件拒绝 | 已实测 | 非法类型不能通过事件协议，测试含负例。 [scheduler_contains_same_minute_cycles_and_keeps_task](tests/test_player_api.py#L127) |
| T12 | 循环封顶、根源与隔离 | 已实测 | 同刻 A/B 循环隔离，保留可检查的来源和任务。 [scheduler_contains_same_minute_cycles_and_keeps_task](tests/test_player_api.py#L127) |
| T13 | 案件跨季与再次检查 | 已实测 | 正式动作跨三季收取新材料，前后来源可追。 [all_cases_can_receive_new_material_after_three_quarters](tests/test_world_v4.py#L336) |
| T14 | 关键询问打断快进 | 已实测 | 预约到刻暂停，未回应时再次快进被拒。 [acquired_evidence_and_formal_ending](tests/test_world_v4.py#L177) |
| T15 | 多级转述原话、版本、送达与来源 | 已实测 | 三次承诺、同季到期与实际传话链均在同一可回放存档内检查，各跳有已送来源与受众。 [c06_f05_three_promises_and_three_person_echo](tests/test_cross_system_routes.py#L161) |
| T16 | 更换实体仍复用 | 部分 | 三项目共享办理，清单验证稳定 ID；替换 ID 的注入复用测试待补。 [register_matches_world_and_all_32_mechanisms](tests/test_world_v4.py#L315) |
| T17 | 中断恢复不重复送达 | 已实测 | SQLite 关闭/重开保存领取与已投递状态，独立消费者重启重试不产生重复通知。 [delivery_after_worker_crash_and_expired_lease](tests/test_delivery_recovery.py#L8) |
| T18 | 同 ID 仅一次提交 | 已实测 | 三路并发返回同一原始回执。 [no_state_change_or_parallel_double_application_for_same_id](tests/test_engine_v4.py#L424) |
| T19 | 任意写点不半更新 | 已实测 | 在含快照写入的真实命令上逐点注入 SQL 失败，逐次比较整份导出并检查可继续提交。 [every_sql_write_position_rolls_back](tests/test_delivery_recovery.py#L69) |
| T20 | 终章仅用取得的证据与历史 | 已实测 | 12 季后依法取得具体记录，调查中的部分知识与正式个人结论保留事件引用；可回放并恢复。 [c09_f08_twelve_seasons_then_independent_acquisition_and_final_finding](tests/test_cross_system_routes.py#L200) |
| T21 | 拒绝伪造人物或文件候选 | 已实测 | 不在可用菜单或无来源的候选不能进入已选结果。 [bounded_advisor_transport_and_fallback](tests/test_player_api.py#L75) |
| T22 | 叙述不接收未获资料 | 已实测 | 四职责的伪服务检查实际传输 JSON，隐藏条目未向模型送出。 [bounded_advisor_transport_and_fallback](tests/test_player_api.py#L75) |
| T23 | 100 种子、十二季与十二不变量 | 已实测 | 100 个不同种子走完 12 季且每局可回放，十二种不变量在其适用点检查。逐项次数与反例测试记录在 BALANCE_CALIBRATION_REPORT.md。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| T24 | 原玩家旅程与恢复 | 部分 | 浏览器旅程包括真实保存恢复；原长局含多个社交和生涯节点的完整串联未逐项确认。 [浏览器旅程](frontend/tests/browser.test.mjs) |

## 架构回归

| 编号 | 要求 | 状态 | 运行证据及边界 |
|---|---|---|---|
| A01 | 缺少物品的高风险尝试 | 已实测 | 实际玩家接口覆盖无物品的确认、取消和拒绝后的有限在场观察，禁止补造物品或无源后果。 [explicit_high_risk_intent_absent_item_and_limited_witnesses](tests/test_player_api.py#L230) |
| A02 | 理智确认取消不改世界 | 已实测 | 实际玩家接口覆盖无物品的确认、取消和拒绝后的有限在场观察，禁止补造物品或无源后果。 [explicit_high_risk_intent_absent_item_and_limited_witnesses](tests/test_player_api.py#L230) |
| A03 | 暂缓签字与约见的部分结果 | 部分 | 批处理实测包含暂缓、被拒与独立后续，原指定双对象组合尚无逐项断言。 [batch_partial_execution_and_causal_dependency](tests/test_player_api.py#L158) |
| A04 | 真实延期与负责人说正常 | 已实测 | 真实三周工程延期，负责人和上级的既有认知不同；跳过汇报后的自主补救在后来资源请求里有来源。 [c01_f01_skip_real_three_week_delay_then_resource_conflict](tests/test_cross_system_routes.py#L51) |
| A05 | 有渠道与无渠道的认知隔离 | 已实测 | 发送之后、送达之前及送达之后对同一接收者断言，仅接收者获取私下记录。 [v4_t10_t14_npc_mail_shares_channel_receipt_gates_belief](tests/test_inspector.py#L12) |
| A06 | 两次转述能回溯 | 已实测 | 三次承诺、同季到期与实际传话链均在同一可回放存档内检查，各跳有已送来源与受众。 [c06_f05_three_promises_and_three_person_echo](tests/test_cross_system_routes.py#L161) |
| A07 | 跨季三项到期顺序 | 部分 | 三项同季到期已实测，关键听证暂停另有测试。特定跨季同刻混合优先序仍未用同一轨迹断言。 [c06_f05_three_promises_and_three_person_echo](tests/test_cross_system_routes.py#L161) |
| A08 | 同命令只增一次版本 | 已实测 | 并发三次检查实收版本、任务数量和历史长度。 [no_state_change_or_parallel_double_application_for_same_id](tests/test_engine_v4.py#L424) |
| A09 | 已承诺资金不可重用 | 已实测 | 确有预留、班组占用与取消释放，有超额反例。 [conditional_budget_and_real_work](tests/test_world_v4.py#L107) |
| A10 | 不得补写旧收礼史 | 部分 | 非法候选/私密资料可过滤；原十年前史料诱导的专用评测待补。 [bounded_advisor_transport_and_fallback](tests/test_player_api.py#L75) |
| A11 | 毁掉原件后副本仍在 | 已实测 | 实体本的异地获取、原件销毁、已取得的独立副本与调查边界在真实提交路径验证。 [c07_f06_removed_original_persists_as_independent_copy](tests/test_cross_system_routes.py#L187) |
| A12 | 模型或事务异常可恢复 | 已实测 | 诱发超时、错误状态、非法数据及越权候选，比对当前世界保持完整；事务层另有真实磁盘满与逐写点试验。 [optional_provider_falls_back_without_mutating_world](tests/test_player_api.py#L276) |
| A13 | 长期案件带来源再次进入 | 已实测 | 跨季取得后续材料并检查案史与依据。 [all_cases_can_receive_new_material_after_three_quarters](tests/test_world_v4.py#L336) |
| A14 | 调任改变联盟 | 已实测 | 核心角色先正式调任，旧联系渠道和盟友利益随后按收到的材料变化。 [c04_f07_old_channel_transfers_then_allied_interests_change](tests/test_cross_system_routes.py#L126) |
| A15 | 100 种子均可读且不变量无违规 | 已实测 | 100 个不同种子走完 12 季且每局可回放，十二种不变量在其适用点检查。逐项次数与反例测试记录在 BALANCE_CALIBRATION_REPORT.md。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| A16 | 拒绝叙事秘密诱导 | 已实测 | 普通玩家投影、旁白输入与 24 人候选菜单均检查私密字段扰动，在线传输回退的额外反例见本地服务测试。 [v4_t32_hidden_ground_truth_cannot_change_visible_actions_or_advisor_input](tests/test_balance_crosscuts.py#L129) |

## 玩法强化验收

| 编号 | 要求 | 状态 | 运行证据及边界 |
|---|---|---|---|
| PLY-01 | 会议与亲自现场检查的时间取舍 | 部分 | 真实旅程限制本人并发活动，未专测同一会议时窗与现场检查冲突。 [service_and_accessible_evidence_with_divergent_paths](tests/test_world_v4.py#L59) |
| PLY-02 | 调查排除至少一种错误解释 | 部分 | 查证确实提供版本/口径反例；玩家能否识别错误解释需求真人观察。 [all_four_frozen_explanations_and_repair](tests/test_world_v4.py#L77) |
| PLY-03 | 完成工序、检查、批准后实际开放路段 | 已实测 | 开放后后续旅行时间变化并保留报告真实性。 [service_and_accessible_evidence_with_divergent_paths](tests/test_world_v4.py#L59) |
| PLY-04 | 无权限不能直接批准 | 已实测 | 缺授权的直接签署被拒，授权与到期实测。 [role_grant_lease_and_reject_forgery](tests/test_world_v4.py#L149) |
| PLY-05 | 两个选择产生不同的下季度项目状态 | 部分 | 有跨季维护与取消后的差异；同一快照的双分支下季度对比待补。 [conditional_budget_and_real_work](tests/test_world_v4.py#L107) |
| PLY-06 | “帮问问”与保证分离 | 已实测 | 同一实际会面中拒绝、问程序与作保证形成不同的正式承诺及后续依赖。 [sc03_three_distinct_speech_obligations](tests/test_scenario_routes_v4.py#L49) |
| PLY-07 | 误传必须有合法消息链 | 已实测 | 三次承诺、同季到期与实际传话链均在同一可回放存档内检查，各跳有已送来源与受众。 [c06_f05_three_promises_and_three_person_echo](tests/test_cross_system_routes.py#L161) |
| PLY-08 | NPC 在玩家未主动接触时行动 | 已实测 | 按时发出工作函，收文经过相同消息服务。 [v4_t10_t14_npc_mail_shares_channel_receipt_gates_belief](tests/test_inspector.py#L12) |
| PLY-09 | 可靠人物不强制背叛 | 部分 | 六弧线有持续合作与其他结局，未穷举各取向的可靠人物保持路径。 [six_character_arcs_have_sourced_intermediate_steps_and_branching_outcomes](tests/test_world_v4.py#L377) |
| PLY-10 | 导师可能过时或正确 | 已实测 | 同一导师依真实消息说出过时建议或已更新的信息，普通会面中可追到其认知变化。 [sc07_mentor_routes_correct_dated_information_and_interest](tests/test_scenario_routes_v4.py#L138) |
| PLY-11 | 四变体产生不同解释 | 已实测 | 一类报告明显夸大，一类新报告正确而旧质疑过时，四条材料结论均核验。 [all_four_frozen_explanations_and_repair](tests/test_world_v4.py#L77) |
| PLY-12 | 临时假说不改变事实 | 部分 | 浏览器脚本比较临时分析前后时间及来源，存档史料也以版本保留。 [浏览器旅程](frontend/tests/browser.test.mjs) |
| PLY-13 | 现场观察有日期及范围 | 已实测 | 可达现场的人实际取得带范围、来源与时间的记录。 [service_and_accessible_evidence_with_divergent_paths](tests/test_world_v4.py#L59) |
| PLY-14 | 公共项目持续发挥作用 | 已实测 | 道路开放改变后续出行，医院开放跨季度产生维护责任。 [conditional_budget_and_real_work](tests/test_world_v4.py#L107) |
| PLY-15 | 同一资源不能重复分配 | 已实测 | 预留支付共用有限预算及班组，取消可释放。 [conditional_budget_and_real_work](tests/test_world_v4.py#L107) |
| PLY-16 | 失去资源后有合法补救 | 部分 | 案件和受限资源均有条件协商，原特定损失后替代办法的对照待补。 [all_cases_can_receive_new_material_after_three_quarters](tests/test_world_v4.py#L336) |
| PLY-17 | 六条人物线可经历不同合法状态 | 已实测 | 普通动作覆盖自主行为、分支和后续记录。 [six_character_arcs_have_sourced_intermediate_steps_and_branching_outcomes](tests/test_world_v4.py#L377) |
| PLY-18 | 十二季以后有两种非调查终局 | 部分 | 照护、死亡、退休有合法长局路径；精确十二季后可选的两种同起点路线未单列。 [late_career_retirement_care_and_health_records](tests/test_world_v4.py#L207) |
| PLY-19 | 早期材料能在后期依法重新解释 | 已实测 | 早期开放记录跨三季重审，档案、见证和限于实际范围三种证据分支产生不同可核后果。 [sc09_three_quarter_old_scope_record_and_three_conditional_review_outcomes](tests/test_scenario_routes_v4.py#L177) |
| PLY-20 | 日常休息不会无提示产生死亡 | 已实测 | 足量日常休息仅按时段和恢复上限改变个人状态；普通休息和主动高风险意图区分，另有真实健康病程。 [m29_m32_family_rest_confirmed_attempt_and_lawful_ending](tests/test_mechanism_contracts_v4.py#L189) |
| PLY-21 | 异常关闭后未消费消息仍可恢复 | 已实测 | SQLite 关闭/重开保存领取与已投递状态，独立消费者重启重试不产生重复通知。 [delivery_after_worker_crash_and_expired_lease](tests/test_delivery_recovery.py#L8) |
| PLY-22 | 回放不重掷、不询问模型 | 已实测 | 仅应用历史效果；恢复原档和分支后逐项比较可见结果。 [integrity_branch_replay_and_wal_backup](tests/test_engine_v4.py#L287) |
| PLY-23 | 浏览器不接收未经取得的材料 | 部分 | 普通 JSON 隔离私密笔记等，全部四类秘密的浏览器/模型/SSE 白名单待测。 [notebook_private_and_clocked_exposure](tests/test_world_v4.py#L129) |
| PLY-24 | 24 个种子均有合法首章前进路线 | 部分 | 100 个预设开局按固定策略成功推进十二季；未对首章所有路线作主观体验判断。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |

## 十二条不变量

| 编号 | 要求 | 状态 | 运行证据及边界 |
|---|---|---|---|
| INV-01 | 世界记录经唯一事务提交 | 已实测 | 1900 次实际提交同时复核日志、收据、状态哈希，领域源码的 SQL 边界与真实 SQLite 故障回滚另行验证。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| INV-02 | 按世界排序并原子更新投影 | 已实测 | 每次校验回放验证世界流序号、哈希和末投影，一致备份有实际测试。 [integrity_branch_replay_and_wal_backup](tests/test_engine_v4.py#L287) |
| INV-03 | 幂等回执、版本不重复增加 | 已实测 | 并发相同命令三次只入一笔。 [no_state_change_or_parallel_double_application_for_same_id](tests/test_engine_v4.py#L424) |
| INV-04 | 人物认知有来源或先验 | 已实测 | 按主体检查新增 Belief 的来源/先验，另测真实收件前后与其他人的私信边界。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| INV-05 | 玩家与模型仅取已获资料 | 已实测 | 每次提交对普通投影断言，检查已获材料与禁见字段；独立模型传输与笔记负例补充。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| INV-06 | 时间单调与旧事先处理 | 已实测 | 整数队列、分段等价与到场暂停经验证。 [v4_t19_t22_opportunity_and_pause](tests/test_engine_v4.py#L255) |
| INV-07 | 资源和占用保持有效 | 已实测 | 逐提交检查预算、支付/预留、班组、工资与可见材料，跨期和角色权限另有负例。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| INV-08 | 案件、调查及终章的事实指控有依据 | 已实测 | 逐提交核对案件、终章及制度认定中的来源，原件/副本与指控分离有独立测试。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| INV-09 | 取消无结果，已观察的失败可以成事实 | 已实测 | 实际玩家接口覆盖无物品的确认、取消和拒绝后的有限在场观察，禁止补造物品或无源后果。 [explicit_high_risk_intent_absent_item_and_limited_witnesses](tests/test_player_api.py#L230) |
| INV-10 | 记录随机槽、条件与裁定 | 已实测 | 12 季轨迹中 100 次实际抽样逐一据槽、候选和种子复算；另有主动篡改已记录结果的负例。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| INV-11 | 极端、调查和终局不绕过硬约束 | 已实测 | 轨迹内检查已结束角色的约束与正式程序；退休、死亡、处分和交接边界另有实际路线。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| INV-12 | 派生深度、频率与循环受限 | 已实测 | 有深度/扇出防护、隔离和队列保留，另见开发 Inspector。 [scheduler_contains_same_minute_cycles_and_keeps_task](tests/test_player_api.py#L127) |

## 八组原始确定性夹具

| 编号 | 要求 | 状态 | 运行证据及边界 |
|---|---|---|---|
| F01 | 工程迟三周，负责人与上级认知不同 | 已实测 | 真实三周工程延期，负责人和上级的既有认知不同；跳过汇报后的自主补救在后来资源请求里有来源。 [c01_f01_skip_real_three_week_delay_then_resource_conflict](tests/test_cross_system_routes.py#L51) |
| F02 | 两份矛盾报告，玩家起初仅有旧版 | 已实测 | 修订后作者和有权核查者取得新版本，玩家仍只持原报告，独立导出与回放保持。 [c05_f02_author_and_auditor_hold_new_version_player_keeps_old](tests/test_cross_system_routes.py#L144) |
| F03 | 未持有相应物品的请求 | 已实测 | 实际玩家接口覆盖无物品的确认、取消和拒绝后的有限在场观察，禁止补造物品或无源后果。 [explicit_high_risk_intent_absent_item_and_limited_witnesses](tests/test_player_api.py#L230) |
| F04 | 多人争用同一预算池 | 已实测 | 两个部门在同一游戏分钟提交请求，争用同一额度及班组。未获全部资源的一方实际修改安排。 [c03_f04_independent_same_minute_department_claims_and_replan](tests/test_cross_system_routes.py#L105) |
| F05 | 三个承诺在一季到期、人物分处不同地点 | 已实测 | 三次承诺、同季到期与实际传话链均在同一可回放存档内检查，各跳有已送来源与受众。 [c06_f05_three_promises_and_three_person_echo](tests/test_cross_system_routes.py#L161) |
| F06 | 记事本留在办公室，访问需真实接触 | 已实测 | 实体本的异地获取、原件销毁、已取得的独立副本与调查边界在真实提交路径验证。 [c07_f06_removed_original_persists_as_independent_copy](tests/test_cross_system_routes.py#L187) |
| F07 | 核心人物调离，部分盟友未获消息 | 已实测 | 核心角色先正式调任，旧联系渠道和盟友利益随后按收到的材料变化。 [c04_f07_old_channel_transfers_then_allied_interests_change](tests/test_cross_system_routes.py#L126) |
| F08 | 部分证据与未证实线索并存 | 已实测 | 12 季后依法取得具体记录，调查中的部分知识与正式个人结论保留事件引用；可回放并恢复。 [c09_f08_twelve_seasons_then_independent_acquisition_and_final_finding](tests/test_cross_system_routes.py#L200) |

## 十条原集成链

| 编号 | 要求 | 状态 | 运行证据及边界 |
|---|---|---|---|
| C01 | 跳过汇报、补救后进入资源冲突 | 已实测 | 真实三周工程延期，负责人和上级的既有认知不同；跳过汇报后的自主补救在后来资源请求里有来源。 [c01_f01_skip_real_three_week_delay_then_resource_conflict](tests/test_cross_system_routes.py#L51) |
| C02 | 私下请求、会面或拒绝与知情者变化 | 已实测 | 普通解析及命令测试私下请求、同意/被拒、未发生时保持未知、披露后相关人知情。 [c02_private_meeting_parser_and_disclosed_or_refused](tests/test_cross_system_routes.py#L75) |
| C03 | 两部门请求、仲裁后调整计划 | 已实测 | 两个部门在同一游戏分钟提交请求，争用同一额度及班组。未获全部资源的一方实际修改安排。 [c03_f04_independent_same_minute_department_claims_and_replan](tests/test_cross_system_routes.py#L105) |
| C04 | 领导调任后利益与支持变化 | 已实测 | 核心角色先正式调任，旧联系渠道和盟友利益随后按收到的材料变化。 [c04_f07_old_channel_transfers_then_allied_interests_change](tests/test_cross_system_routes.py#L126) |
| C05 | 旧版保留，调查员取得新版 | 已实测 | 修订后作者和有权核查者取得新版本，玩家仍只持原报告，独立导出与回放保持。 [c05_f02_author_and_auditor_hold_new_version_player_keeps_old](tests/test_cross_system_routes.py#L144) |
| C06 | 传闻经多名人物返回玩家 | 已实测 | 三次承诺、同季到期与实际传话链均在同一可回放存档内检查，各跳有已送来源与受众。 [c06_f05_three_promises_and_three_person_echo](tests/test_cross_system_routes.py#L161) |
| C07 | 销毁原本而副本保留且不自动认定 | 已实测 | 实体本的异地获取、原件销毁、已取得的独立副本与调查边界在真实提交路径验证。 [c07_f06_removed_original_persists_as_independent_copy](tests/test_cross_system_routes.py#L187) |
| C08 | 理智确认后再验高风险行动 | 已实测 | 实际玩家接口覆盖无物品的确认、取消和拒绝后的有限在场观察，禁止补造物品或无源后果。 [explicit_high_risk_intent_absent_item_and_limited_witnesses](tests/test_player_api.py#L230) |
| C09 | 十多季度后取得线索进入终章 | 已实测 | 12 季后依法取得具体记录，调查中的部分知识与正式个人结论保留事件引用；可回放并恢复。 [c09_f08_twelve_seasons_then_independent_acquisition_and_final_finding](tests/test_cross_system_routes.py#L200) |
| C10 | 模型杜撰未登记候选被拒 | 已实测 | 真实本地 HTTP 假服务返回未登记 key，输入与世界都未接纳伪造候选。 [bounded_advisor_transport_and_fallback](tests/test_player_api.py#L75) |

## 数据库故障与恢复

| 编号 | 要求 | 状态 | 运行证据及边界 |
|---|---|---|---|
| DB-01 | 提交同命令三次仅一组事件 | 已实测 | 三并发提交核验队列长度和记录数。 [no_state_change_or_parallel_double_application_for_same_id](tests/test_engine_v4.py#L424) |
| DB-02 | 逐一注入事务每个写点 | 已实测 | 在含快照写入的真实命令上逐点注入 SQL 失败，逐次比较整份导出并检查可继续提交。 [every_sql_write_position_rolls_back](tests/test_delivery_recovery.py#L69) |
| DB-03 | 规则版本与随机记录持久化 | 已实测 | 完整导出里的槽、候选、权重和绑定参数用于独立对照。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| DB-04 | 历史重建等于存储投影 | 已实测 | 验证链式校验，含丢/坏快照后的回放。 [integrity_branch_replay_and_wal_backup](tests/test_engine_v4.py#L287) |
| DB-05 | 并发相同版本互斥 | 已实测 | 一个成功，另一个收到可识别版本冲突。 [v4_t17_atomicity_concurrency_idempotence](tests/test_engine_v4.py#L217) |
| DB-06 | Outbox 重试不重复送达 | 已实测 | 实际 SQLite 通知 Outbox 经领单未执行、过租期再领、已执行未 ACK 及重复确认；给公开 feed 的版本只出现一次。人物收件在世界事务内单次记账。 [delivery_after_worker_crash_and_expired_lease](tests/test_delivery_recovery.py#L8) |

## 补充验收

| 编号 | 要求 | 状态 | 运行证据及边界 |
|---|---|---|---|
| NEW-01 | 同命令 ID 不同内容 | 已实测 | 冲突无新世界变化。 [v4_t17_atomicity_concurrency_idempotence](tests/test_engine_v4.py#L217) |
| NEW-02 | 丢失回执后携旧版本重发 | 已实测 | 先匹配幂等回执。 [v4_t17_atomicity_concurrency_idempotence](tests/test_engine_v4.py#L217) |
| NEW-03 | 重核后旧确认令牌不能提交 | 部分 | 已实测绑定 revision 与条款的 HMAC、篡改/过期拒绝。独立 Proposal generation 的重核继承尚需单列证据。 [confirmation_binds_terms_revision_and_receipt](tests/test_player_api.py#L200) |
| NEW-04 | 纯 Resolver 同快照逐字段相同 | 已实测 | 相同快照执行真实跨季 Resolver 两次，守卫禁止文件/数据库/网络、系统钟、外部进程与随机熵，并逐项比较状态和事件。 [v4_t11_resolver_tape_is_pure_under_io_clock_and_entropy_guards](tests/test_balance_crosscuts.py#L38) |
| NEW-05 | NPC 可基于过时资源认知行动 | 部分 | 菜单隔离和硬权限有实测，原误信资源的尝试/反馈对照待测。 [bounded_advisor_transport_and_fallback](tests/test_player_api.py#L75) |
| NEW-06 | 失败依赖被阻断，独立动作仍可执行 | 已实测 | 两项同名冲突和两个不同依赖均有逐子动作结果。 [batch_partial_execution_and_causal_dependency](tests/test_player_api.py#L158) |
| NEW-07 | Outbox 领取后崩溃可重新领 | 已实测 | 实际 SQLite 通知 Outbox 经领单未执行、过租期再领、已执行未 ACK 及重复确认；给公开 feed 的版本只出现一次。人物收件在世界事务内单次记账。 [delivery_after_worker_crash_and_expired_lease](tests/test_delivery_recovery.py#L8) |
| NEW-08 | 效果提交与 ack 之间崩溃不重复送达 | 已实测 | 实际 SQLite 通知 Outbox 经领单未执行、过租期再领、已执行未 ACK 及重复确认；给公开 feed 的版本只出现一次。人物收件在世界事务内单次记账。 [delivery_after_worker_crash_and_expired_lease](tests/test_delivery_recovery.py#L8) |
| NEW-09 | 较早截止打断长推进 | 已实测 | 听证等关键节点暂停，未回应不能继续。 [v4_t19_t22_opportunity_and_pause](tests/test_engine_v4.py#L255) |
| NEW-10 | 迟到叙事不能覆盖新界面 | 部分 | 有双标签页 SSE 上下文同步脚本；故意逆序的延迟叙事试验待核。 [浏览器旅程](frontend/tests/browser.test.mjs) |
| NEW-11 | 本人异地无法向原笔记本写入 | 已实测 | 离开办公桌后可见投影无原文，动作需实际取回。 [notebook_private_and_clocked_exposure](tests/test_world_v4.py#L129) |
| NEW-12 | 同处一地不等于读过笔记 | 部分 | 获取与持有独立检查；指定配偶单纯在场而不接触的负例仍需专门路径。 [c07_f06_removed_original_persists_as_independent_copy](tests/test_cross_system_routes.py#L187) |
| NEW-13 | 未经见证的原件销毁不自动定罪 | 已实测 | 私下毁掉原件不生成认定，已经有合法取得链的独立副本仍可留存；他人获知取决于接触来源。 [sc08_same_note_is_private_read_or_preserved_by_different_actions](tests/test_scenario_routes_v4.py#L153) |
| NEW-14 | 导师建议按自己取得的材料 | 已实测 | 同一导师依真实消息说出过时建议或已更新的信息，普通会面中可追到其认知变化。 [sc07_mentor_routes_correct_dated_information_and_interest](tests/test_scenario_routes_v4.py#L138) |
| NEW-15 | 向导师实际出示一条笔记 | 待测 | 需要完整出示事件、导师观察和来源的专门旅程。 [notebook_private_and_clocked_exposure](tests/test_world_v4.py#L129) |
| NEW-16 | 安全窗边正常休息 | 已实测 | 足量日常休息仅按时段和恢复上限改变个人状态；普通休息和主动高风险意图区分，另有真实健康病程。 [m29_m32_family_rest_confirmed_attempt_and_lawful_ending](tests/test_mechanism_contracts_v4.py#L189) |
| NEW-17 | 危险窗边既存环境与可感信号 | 待测 | 没有针对该特殊事件的正式回归证据。 待外部证据 |
| NEW-18 | 阻断外网后核心游戏完整 | 已实测 | 阻断 socket 外连，五个锚点真实走遍九地点、三项目验收开放、导师、实体本、12 季、主动离开及异库恢复。配置不可达提供方的配对世界与离线世界逐步相同。 [v4_t31_all_scenes_projects_mentors_and_ending_with_network_blocked](tests/test_balance_crosscuts.py#L167) |
| NEW-19 | 否定和歧义不能偷偷变动作 | 已实测 | 无确认的歧义输入不会直接提交。 [visible_parser_does_not_reverse_intent](tests/test_player_api.py#L69) |
| NEW-20 | 旁白不能创造新的 NPC 承诺 | 已实测 | 只在登记的可见选项中选择，伪造候选降级。 [bounded_advisor_transport_and_fallback](tests/test_player_api.py#L75) |
| NEW-21 | WAL 导出或中断不破坏前一备份 | 已实测 | 真实在线备份与替换中断对原备份字节比较。 [disk_full_rolls_back_and_backup_replace_is_atomic](tests/test_engine_v4.py#L324) |
| NEW-22 | 缺快照、旧规则、未来存档 | 部分 | 本产品旧 SQLite 结构先备份、迁移重建 feed，缺快照可回放。规格 V3 实际存档仍缺迁移样本。 [schema_migration_rebuilds_feed_and_protects_original](tests/test_delivery_recovery.py#L47) |
| NEW-23 | 从旧点创建独立分支 | 已实测 | 继承不可变历史，父世界维持原进度，旧档重复导入不生成重复分支。 [integrity_branch_replay_and_wal_backup](tests/test_engine_v4.py#L287) |
| NEW-24 | 八起点和八终局由普通行动可达 | 部分 | 多项常规起点和全部终局有实测；所有终章局部夹具与起点×终局矩阵另核。 [late_career_retirement_care_and_health_records](tests/test_world_v4.py#L207) |
| NEW-25 | 24 人物、16 案件、32 机制 | 部分 | 清单与多条真实路径已查；更换实体和每个机制的单独负例仍待补证。 [register_matches_world_and_all_32_mechanisms](tests/test_world_v4.py#L315) |
| NEW-26 | 十二季档案后继续生涯 | 已实测 | 100 局到达第十三季开头，长局继续至有效退休。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| NEW-27 | 120 季度边界 | 已实测 | 年轻角色走满 120 季、回放一致并继续至自然退休。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| NEW-28 | 源码、浏览器、Mac、真实模型分别记录 | 部分 | 当前分开核验，平台与模型线上实测须使用各自的记录。 [macOS 构建](scripts/build_macos.sh) |
| NEW-29 | 发行包无真实 Inspector 接口 | 部分 | 开发工具独立且保留源档。发行包路由负例待平台记录。 [inspector_isolated_json_and_sqlite_and_old_version](tests/test_inspector.py#L54) |
| NEW-30 | 文书提示词和玩家文字不产生系统权限 | 部分 | 严格菜单与动作的语义过滤有验证；各类恶意文书组合未逐条测试。 [bounded_advisor_transport_and_fallback](tests/test_player_api.py#L75) |
| NEW-31 | 中文 IME、键盘与字号 | 部分 | 浏览器脚本有键盘与输入覆盖；真实系统输入法与读屏记录另核。 [浏览器旅程](frontend/tests/browser.test.mjs) |
| NEW-32 | 未知类型、坏 ID、缺模板 | 部分 | 未知事件/无权实体有负例；内容清单缺模板的构建故障须单测。 [scheduler_contains_same_minute_cycles_and_keeps_task](tests/test_player_api.py#L127) |

## 判定与事件模块

| 编号 | 要求 | 状态 | 运行证据及边界 |
|---|---|---|---|
| J1 | J1 意图归一化与动作依赖 | 部分 | 已验证结构化批次与歧义；指定 20 组自然语言组合需要完整覆盖。 [batch_partial_execution_and_causal_dependency](tests/test_player_api.py#L158) |
| J2 | J2 硬约束 | 部分 | 授权、物品、地点、日程和程序都有实际约束；原验证器注册与全矩阵待核。 [role_grant_lease_and_reject_forgery](tests/test_world_v4.py#L149) |
| J3 | J3 资源仲裁 | 部分 | 同池和部分分配实测。两 NPC 同时争不可分资源的专门对照待补。 [conditional_budget_and_real_work](tests/test_world_v4.py#L107) |
| J4 | J4 自主反应 | 部分 | 实际联系和候选过滤有证据；私密动机与所有回应类别需更多条件组合。 [bounded_advisor_transport_and_fallback](tests/test_player_api.py#L75) |
| J5 | J5 稳定随机裁定 | 已实测 | 实际七点配对与 10000 次固定分布采样，存档保留非显示的审计依据。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| J6 | J6 复合动作与部分完成 | 部分 | 子动作独立返回与依赖阻断实测，失败但可见的尝试见 T07。 [batch_partial_execution_and_causal_dependency](tests/test_player_api.py#L158) |
| J7 | J7 任职、空缺、考察与任命 | 已实测 | 普通动作完成正式岗位链；任命有资格与组织条件。 [cooperation_materials_sustain_a_complete_position_chain](tests/test_world_v4.py#L256) |
| J8 | J8 调查、证据、指控与制度认定 | 已实测 | 取得、程序、听证、书面结论和两个不同后果在角色旅程中区分。 [acquired_evidence_and_formal_ending](tests/test_world_v4.py#L177) |
| J9 | J9 高影响事项、健康与终局 | 部分 | 八终局、确认与交接均有路径；根据原特殊夹具逐项裁决见 A01、NEW-17。 [late_career_retirement_care_and_health_records](tests/test_world_v4.py#L207) |
| E1 | E1 已登记的事件合同 | 已实测 | 未知事件被拒，秘密审计事件不能成为公开叙述。 [scheduler_contains_same_minute_cycles_and_keeps_task](tests/test_player_api.py#L127) |
| E2 | E2 触发、订阅与资格 | 部分 | 实际符合资格的进展有回归，来源版通用订阅表缺独立覆盖。 [all_cases_can_receive_new_material_after_three_quarters](tests/test_world_v4.py#L336) |
| E3 | E3 派生与因果来源 | 已实测 | 同刻循环有来源链、界限和隔离记录。 [scheduler_contains_same_minute_cycles_and_keeps_task](tests/test_player_api.py#L127) |
| E4 | E4 跨期案件 | 已实测 | 16 案件有状态变化、来源、后续复查与条件反例。 [all_cases_can_receive_new_material_after_three_quarters](tests/test_world_v4.py#L336) |
| E5 | E5 调度与快进 | 已实测 | 整分钟排序、切片等价、截止和必须决策的暂停被核实。 [v4_t19_t22_opportunity_and_pause](tests/test_engine_v4.py#L255) |
| E6 | E6 人物唤醒 | 部分 | 自主寄件、收件和角色既有计划实测；全体人物多来源的唤醒合并策略待补。 [v4_t10_t14_npc_mail_shares_channel_receipt_gates_belief](tests/test_inspector.py#L12) |
| E7 | E7 通信和认知更新 | 已实测 | 消息绑定渠道时延、逐跳来源和内容，受众仅在送达后纳入本人信念。 [c06_f05_three_promises_and_three_person_echo](tests/test_cross_system_routes.py#L161) |
| E8 | E8 八个机制族 | 部分 | 内容目录与实际业务路径可查；换实体 ID 的通用性尚未逐族检验。 [register_matches_world_and_all_32_mechanisms](tests/test_world_v4.py#L315) |
| E9 | E9 事务、恢复与审计 | 已实测 | 领单崩溃、重领、应用后未 ACK、去重并恢复，对照 Inspector 与回放。 [delivery_after_worker_crash_and_expired_lease](tests/test_delivery_recovery.py#L8) |
| E10 | E10 循环诊断与隔离 | 已实测 | 同刻派生循环受控并保留隔离任务，Inspector 可见诊断。 [scheduler_contains_same_minute_cycles_and_keeps_task](tests/test_player_api.py#L127) |

## 桌面发行与真实参与者

本节由负责目标安装包与真人门槛的最终验收人补充。记录构建版本、哈希、OS/架构、启动/存取档范围、网络条件及实际参与情况。
