# 《局中事》验收记录

本次交付为 Apple Silicon Mac 本地功能候选。连续参数和发布依据是 V4.0 第 12–13 章，历史门槛沿用 S30 第 14–15 章与 S31 第 46 页的原编号。已有存档的兼容范围、模型来源和真人参与情况见文末发行记录。

## 如何复核

- [需求证据矩阵](REQUIREMENTS_TRACEABILITY.csv) 保留 423 条内嵌历史来源。历史行保留原 ID、原文件、原页和条文。适用的软件验收行另列当前门槛、实现与复核命令。来源中的封面、风险登记、开发建议和延期范围不作为软件通过项。标为“原条款待逐项核对”的行只建立了关联入口。
- 在仓库根运行 `.venv/bin/python -m pytest --disable-warnings -q`。本次完整回归结果见文末发行记录。表内源码测试链接可直接定位断言。CSV 的命令列提供可单独执行的 pytest 节点。
- 运行 `.venv/bin/python scripts/calibrate.py --json /tmp/jzs-calibration.json --report BALANCE_CALIBRATION_REPORT.md` 复核 100 种子、12 季、120 季、配对数值与模拟不变量。系统及代码指纹、各条件的观测与范围见[实测报告](BALANCE_CALIBRATION_REPORT.md)。
- 进入 `frontend` 后运行 `JZS_TEST_APP="$PWD/../release/局中事.app" npm run test:e2e` 复核包内游戏。在同一命令前加上 `JZS_BROWSER=webkit` 可使用 WebKit。原生窗口操作另见文末发行记录。

“已实测”表示行内所述条件已有实际断言或观测。“部分”列出尚缺的原场景、统计边界或验证层。“待测”保留有明确通过标准而未取得证据的条款。相同测试可支撑多个来源编号，门槛不能按测试总数推算。

## 外部与兼容边界

- V3.0/V3.1 正式游戏存档原件尚未提供。本产品 SQLite 旧结构、坏/缺快照、原型识别及备份恢复已有实际检查。[兼容范围](SAVE_COMPATIBILITY.md)
- 数学、脚本策略、模型替身和实际本机模型调用分别记录。首轮六人轮换试玩的实际参与数为零。[真人试玩记录](PLAYTEST_REPORT.md)

## 放行门槛

| 编号 | 要求 | 状态 | 运行证据及边界 |
|---|---|---|---|
| G0 | 契约冻结与来源映射 | 部分 | 外部合同和内容注册已有负例，F01–F08 的输入与结果见下表。世界内部以领域字典存储，部分对象缺独立类型合同。 [测试文件](tests/test_content_validation.py) |
| G1 | 提交、持久化、重放与恢复 | 已实测 | 幂等、版本冲突、每个写点故障、快照重建与回放分别见 DB-01 至 DB-05。队列随世界事务持久化，SQLite 通知 Outbox 的重领和去重见 DB-06。 [every_sql_write_position_rolls_back](tests/test_delivery_recovery.py#L69) |
| G2 | J1–J9 判定 | 部分 | 意图依赖、撤回或重核、有限见证和持物条件分别见 J1、NEW-03、T07。部分模块的注册及边界覆盖见 J2 至 J9。 [j1_compound_negation_reference_and_condition_matrix](tests/test_player_api.py#L385) |
| G3 | E1–E10 事件 | 部分 | 定时、传播、案件、同刻隔离和可重领的通知队列有运行证据。原通用订阅合同及多来源人物唤醒覆盖见 E2、E6。 [delivery_after_worker_crash_and_expired_lease](tests/test_delivery_recovery.py#L8) |
| G4 | 互操作与 100 种子十二季 | 已实测 | 原 C01–C10 已有完整来源路径或专门接口试验。100 局十二季逐步执行十二类不变量检查，120 季观察单列数值报告。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| G5 | 四类 AI 角色与离线降级 | 已实测 | 本机 gpt-oss-120b 服务对解析、人物、案件、旁白分别返回已登记候选。世界状态一致且可回放。非法响应与断网回退分别由单独测试验证。云端提供方未测。 [四类模型角色的实机复核](scripts/verify_model.py) |
| G6 | 普通玩家界面完整旅程 | 已实测 | 普通界面覆盖三种听汇报方式、四种邀请回复、两轮交谈、导师与家庭、笔记本的异地取回和副本。实际推进十二季、关掉页面重开，再通过调任交接进入 END04。存档恢复和八个起点另有旅程。 [发行包浏览器测试](frontend/tests/browser.test.mjs) |
| G7 | 硬化、迁移、原测试与发布条件 | 部分 | T01–T24、事务和恢复分项见表。实际 V3 存档未提供，部分历史领域合同和原层级断言仍待专门核验。 [integrity_branch_replay_and_wal_backup](tests/test_engine_v4.py#L287) |
| G8 | 全部世界内容与交互边界 | 部分 | 八起点和八终局的 64 条轨迹通过。十场景、六人物线、16 案和 32 机制有专门断言。八族机制的实体替换范围与人工审阅仍分项记录。 [ending_from_registered_start_and_final_checkpoint](tests/test_ending_routes.py#L54) |
| G9 | 本机发行、分发与反馈 | 部分 | Apple Silicon 发行包已在本机实际启动／恢复。八个同时冷启动的实例只留下一个窗口与引擎。缺乏独立新机器上的安装记录，Apple 公证及真人体验状态见文末。 [发行包浏览器测试](frontend/tests/browser.test.mjs) |

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
| T03 | 预算不双花 | 已实测 | 两个部门在同一游戏分钟提交请求，争用同一额度及班组。未获全部资源的一方实际修改安排。 [c03_f04_independent_same_minute_department_claims_and_replan](tests/test_cross_system_routes.py#L106) |
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
| T15 | 多级转述原话、版本、送达与来源 | 已实测 | 三次承诺、同季到期与实际传话链均在同一可回放存档内检查，各跳有已送来源与受众。 [c06_f05_three_promises_and_three_person_echo](tests/test_cross_system_routes.py#L162) |
| T16 | 更换实体仍复用 | 已实测 | 将登记项目和主管替换为 P90、N90。常规办理先因未会签受阻，补齐后按同一资金和班组规则施工、验收、批准并转入二期。24 人、16 案、32 机制另见清单和各机制回归。 [substituted_project_and_owner_from_registration_through_next_phase](tests/test_project_substitution.py#L12) |
| T17 | 中断恢复不重复送达 | 已实测 | SQLite 关闭/重开保存领取与已投递状态，独立消费者重启重试不产生重复通知。 [delivery_after_worker_crash_and_expired_lease](tests/test_delivery_recovery.py#L8) |
| T18 | 同 ID 仅一次提交 | 已实测 | 三路并发返回同一原始回执。 [no_state_change_or_parallel_double_application_for_same_id](tests/test_engine_v4.py#L424) |
| T19 | 任意写点不半更新 | 已实测 | 在含快照写入的真实命令上逐点注入 SQL 失败，逐次比较整份导出并检查可继续提交。 [every_sql_write_position_rolls_back](tests/test_delivery_recovery.py#L69) |
| T20 | 终章仅用取得的证据与历史 | 已实测 | 12 季后依法取得具体记录，调查中的部分知识与正式个人结论保留事件引用；可回放并恢复。 [c09_f08_twelve_seasons_then_independent_acquisition_and_final_finding](tests/test_cross_system_routes.py#L201) |
| T21 | 拒绝伪造人物或文件候选 | 已实测 | 不在可用菜单或无来源的候选不能进入已选结果。 [bounded_advisor_transport_and_fallback](tests/test_player_api.py#L75) |
| T22 | 叙述不接收未获资料 | 已实测 | 四职责的伪服务检查实际传输 JSON，隐藏条目未向模型送出。 [bounded_advisor_transport_and_fallback](tests/test_player_api.py#L75) |
| T23 | 100 种子、十二季与十二不变量 | 已实测 | 100 个不同种子走完 12 季且每局可回放，十二种不变量在其适用点检查。逐项次数与反例测试记录在 BALANCE_CALIBRATION_REPORT.md。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| T24 | 原玩家旅程与恢复 | 已实测 | 普通界面覆盖三种听汇报方式、四种邀请回复、两轮交谈、导师与家庭、笔记本的异地取回和副本。实际推进十二季、关掉页面重开，再通过调任交接进入 END04。存档恢复和八个起点另有旅程。 [发行包浏览器测试](frontend/tests/browser.test.mjs) |

## 架构回归

| 编号 | 要求 | 状态 | 运行证据及边界 |
|---|---|---|---|
| A01 | 缺少物品的高风险尝试 | 已实测 | 实际玩家接口覆盖无物品的确认、取消和拒绝后的有限在场观察，禁止补造物品或无源后果。 [explicit_high_risk_intent_absent_item_and_limited_witnesses](tests/test_player_api.py#L230) |
| A02 | 理智确认取消不改世界 | 已实测 | 实际玩家接口覆盖无物品的确认、取消和拒绝后的有限在场观察，禁止补造物品或无源后果。 [explicit_high_risk_intent_absent_item_and_limited_witnesses](tests/test_player_api.py#L230) |
| A03 | 暂缓签字与约见的部分结果 | 已实测 | 原句“先不签字，今晚问老周为什么换了附件。”解析为暂缓答复与向周主任核对附件的请求。未唯一指认的同姓者需澄清。重复暂缓失败不阻挡新约见。另见 tests/test_world_disclosures.py 的赴约、异地错过和送达过迟路径。 [a03_defer_signature_and_ask_zhou_without_presuming_a_fact](tests/test_player_api.py#L450) |
| A04 | 真实延期与负责人说正常 | 已实测 | 真实三周工程延期，负责人和上级的既有认知不同；跳过汇报后的自主补救在后来资源请求里有来源。 [c01_f01_skip_real_three_week_delay_then_resource_conflict](tests/test_cross_system_routes.py#L52) |
| A05 | 有渠道与无渠道的认知隔离 | 已实测 | 发送之后、送达之前及送达之后对同一接收者断言，仅接收者获取私下记录。 [v4_t10_t14_npc_mail_shares_channel_receipt_gates_belief](tests/test_inspector.py#L12) |
| A06 | 两次转述能回溯 | 已实测 | 三次承诺、同季到期与实际传话链均在同一可回放存档内检查，各跳有已送来源与受众。 [c06_f05_three_promises_and_three_person_echo](tests/test_cross_system_routes.py#L162) |
| A07 | 跨季三项到期顺序 | 已实测 | 在跨季快进中，材料比对、联络回函及独立材料分别在原定的三个时点送达。听证拦下后续审批，明确答复后才继续办理。存档可回放并恢复。 [three_deadlines_cross_quarter_and_pause_before_later_work](tests/test_quarter_deadlines.py#L11) |
| A08 | 同命令只增一次版本 | 已实测 | 并发三次检查实收版本、任务数量和历史长度。 [no_state_change_or_parallel_double_application_for_same_id](tests/test_engine_v4.py#L424) |
| A09 | 已承诺资金不可重用 | 已实测 | 确有预留、班组占用与取消释放，有超额反例。 [conditional_budget_and_real_work](tests/test_world_v4.py#L107) |
| A10 | 不得补写旧收礼史 | 已实测 | 要求自己获得审批权的文字只作为私人笔记保存，角色权限、财政、文书均不变。模型虚构十年前的收礼记录时，旁白回退，导出历史保持原样。 [player_words_and_model_invention_have_no_world_authority](tests/test_player_text_boundaries.py#L10) |
| A11 | 毁掉原件后副本仍在 | 已实测 | 实体本的异地获取、原件销毁、已取得的独立副本与调查边界在真实提交路径验证。 [c07_f06_removed_original_persists_as_independent_copy](tests/test_cross_system_routes.py#L188) |
| A12 | 模型或事务异常可恢复 | 已实测 | 诱发超时、错误状态、非法数据及越权候选，比对当前世界保持完整；事务层另有真实磁盘满与逐写点试验。 [optional_provider_falls_back_without_mutating_world](tests/test_player_api.py#L276) |
| A13 | 长期案件带来源再次进入 | 已实测 | 跨季取得后续材料并检查案史与依据。 [all_cases_can_receive_new_material_after_three_quarters](tests/test_world_v4.py#L336) |
| A14 | 调任改变联盟 | 已实测 | 核心角色先正式调任，旧联系渠道和盟友利益随后按收到的材料变化。 [c04_f07_old_channel_transfers_then_allied_interests_change](tests/test_cross_system_routes.py#L127) |
| A15 | 100 种子均可读且不变量无违规 | 已实测 | 100 个不同种子走完 12 季且每局可回放，十二种不变量在其适用点检查。逐项次数与反例测试记录在 BALANCE_CALIBRATION_REPORT.md。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| A16 | 拒绝叙事秘密诱导 | 已实测 | 普通玩家投影、旁白输入与 24 人候选菜单均检查私密字段扰动，在线传输回退的额外反例见本地服务测试。 [v4_t32_hidden_ground_truth_cannot_change_visible_actions_or_advisor_input](tests/test_balance_crosscuts.py#L129) |

## 玩法强化验收

| 编号 | 要求 | 状态 | 运行证据及边界 |
|---|---|---|---|
| PLY-01 | 会议与亲自现场检查的时间取舍 | 已实测 | 从同一开局比较 45 分钟会议与完整现场往返。用首个 240 分钟截止检验实际日程取舍。 [opening_meeting_and_round_trip_compete_for_the_same_deadline](tests/test_playability_choices.py#L8) |
| PLY-02 | 调查排除至少一种错误解释 | 已实测 | 两个初始简报和旧摘录文字相同。玩家在现场获得有日期、范围及出处的分项材料：一局的同日账本排除“已完成40”，另一局的最新交接单排除“仍只有20”。 [same_visible_claim_can_be_ruled_out_or_confirmed_with_dated_records](tests/test_playability_choices.py#L95) |
| PLY-03 | 完成工序、检查、批准后实际开放路段 | 已实测 | 开放后后续旅行时间变化并保留报告真实性。 [service_and_accessible_evidence_with_divergent_paths](tests/test_world_v4.py#L59) |
| PLY-04 | 无权限不能直接批准 | 已实测 | 缺授权的直接签署被拒，授权与到期实测。 [role_grant_lease_and_reject_forgery](tests/test_world_v4.py#L149) |
| PLY-05 | 两个选择产生不同的下季度项目状态 | 已实测 | 同一已存报价分为承接与撤回，推进至次季。前者南渠分段验收并产生实付及维护，后者仍待议且实付为零；两条分支均回放验证。 [funding_decisions_from_same_saved_offer_diverge_next_quarter](tests/test_cross_system_routes.py#L266) |
| PLY-06 | “帮问问”与保证分离 | 已实测 | 同一实际会面中拒绝、问程序与作保证形成不同的正式承诺及后续依赖。 [sc03_three_distinct_speech_obligations](tests/test_scenario_routes_v4.py#L49) |
| PLY-07 | 误传必须有合法消息链 | 已实测 | 三次承诺、同季到期与实际传话链均在同一可回放存档内检查，各跳有已送来源与受众。 [c06_f05_three_promises_and_three_person_echo](tests/test_cross_system_routes.py#L162) |
| PLY-08 | NPC 在玩家未主动接触时行动 | 已实测 | 按时发出工作函，收文经过相同消息服务。 [v4_t10_t14_npc_mail_shares_channel_receipt_gates_belief](tests/test_inspector.py#L12) |
| PLY-09 | 可靠人物不强制背叛 | 已实测 | 在 0、0.25、0.5、0.75 和 1 五个取向，技术员都可依约留任、提供署名的准确分项材料并完成现场检查。 [trusted_technician_can_keep_the_appointment_and_deliver_accurate_evidence](tests/test_playability_choices.py#L81) |
| PLY-10 | 导师可能过时或正确 | 已实测 | 同一导师依真实消息说出过时建议或已更新的信息，普通会面中可追到其认知变化。 [sc07_mentor_routes_correct_dated_information_and_interest](tests/test_scenario_routes_v4.py#L138) |
| PLY-11 | 四变体产生不同解释 | 已实测 | 一类报告明显夸大，一类新报告正确而旧质疑过时，四条材料结论均核验。 [all_four_frozen_explanations_and_repair](tests/test_world_v4.py#L77) |
| PLY-12 | 临时假说不改变事实 | 已实测 | 写下虚假假说后取得独立材料，原初事实不变。异地失去原本时无法读取，返程取回后可合法制作签收副本。临时草稿另有浏览器检查。 [unverified_hypothesis_and_recoverable_loss_of_source](tests/test_playability_choices.py#L28) |
| PLY-13 | 现场观察有日期及范围 | 已实测 | 可达现场的人实际取得带范围、来源与时间的记录。 [service_and_accessible_evidence_with_divergent_paths](tests/test_world_v4.py#L59) |
| PLY-14 | 公共项目持续发挥作用 | 已实测 | 道路开放改变后续出行，医院开放跨季度产生维护责任。 [conditional_budget_and_real_work](tests/test_world_v4.py#L107) |
| PLY-15 | 同一资源不能重复分配 | 已实测 | 预留支付共用有限预算及班组，取消可释放。 [conditional_budget_and_real_work](tests/test_world_v4.py#L107) |
| PLY-16 | 失去资源后有合法补救 | 已实测 | 写下虚假假说后取得独立材料，原初事实不变。异地失去原本时无法读取，返程取回后可合法制作签收副本。临时草稿另有浏览器检查。 [unverified_hypothesis_and_recoverable_loss_of_source](tests/test_playability_choices.py#L28) |
| PLY-17 | 六条人物线可经历不同合法状态 | 已实测 | 普通动作覆盖自主行为、分支和后续记录。 [six_character_arcs_have_sourced_intermediate_steps_and_branching_outcomes](tests/test_world_v4.py#L377) |
| PLY-18 | 十二季以后有两种非调查终局 | 已实测 | 相同起点与种子过完十二季，再分别通过离任和调任申请完成交接，走到两种非调查终局。 [twelve_completed_quarters_allow_two_noninvestigative_endings](tests/test_playability_choices.py#L44) |
| PLY-19 | 早期材料能在后期依法重新解释 | 已实测 | 早期开放记录跨三季重审，档案、见证和限于实际范围三种证据分支产生不同可核后果。 [sc09_three_quarter_old_scope_record_and_three_conditional_review_outcomes](tests/test_scenario_routes_v4.py#L177) |
| PLY-20 | 日常休息不会无提示产生死亡 | 已实测 | 足量日常休息仅按时段和恢复上限改变个人状态；普通休息和主动高风险意图区分，另有真实健康病程。 [m29_m32_family_rest_confirmed_attempt_and_lawful_ending](tests/test_mechanism_contracts_v4.py#L189) |
| PLY-21 | 异常关闭后未消费消息仍可恢复 | 已实测 | SQLite 关闭/重开保存领取与已投递状态，独立消费者重启重试不产生重复通知。 [delivery_after_worker_crash_and_expired_lease](tests/test_delivery_recovery.py#L8) |
| PLY-22 | 回放不重掷、不询问模型 | 已实测 | 仅应用历史效果；恢复原档和分支后逐项比较可见结果。 [integrity_branch_replay_and_wal_backup](tests/test_engine_v4.py#L287) |
| PLY-23 | 浏览器不接收未经取得的材料 | 已实测 | 在饭局以普通玩家会话读取当前投影、可见历史、回顾与真实 SSE 消息，逐一检查未持有的本子原文、内部排期、NPC 信念、病程窗口、种子和真相编号均未传出。模型菜单的认知隔离另见 V4-T32。 [发行包浏览器测试](frontend/tests/browser.test.mjs) |
| PLY-24 | 24 个种子均有合法首章前进路线 | 已实测 | 预定 24 个不同种子轮换 8 个出身，均完成开局履约、现场取证，并按普通玩家当时可见的菜单逐步办理检查、必要整改、批准和通行。全部在首季实际开放。 [twenty_four_opening_seeds_can_deliver_the_first_safe_crossing](tests/test_playability_choices.py#L54) |

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
| F01 | 工程迟三周，负责人与上级认知不同 | 已实测 | 真实三周工程延期，负责人和上级的既有认知不同；跳过汇报后的自主补救在后来资源请求里有来源。 [c01_f01_skip_real_three_week_delay_then_resource_conflict](tests/test_cross_system_routes.py#L52) |
| F02 | 两份矛盾报告，玩家起初仅有旧版 | 已实测 | 修订后作者和有权核查者取得新版本，玩家仍只持原报告，独立导出与回放保持。 [c05_f02_author_and_auditor_hold_new_version_player_keeps_old](tests/test_cross_system_routes.py#L145) |
| F03 | 未持有相应物品的请求 | 已实测 | 实际玩家接口覆盖无物品的确认、取消和拒绝后的有限在场观察，禁止补造物品或无源后果。 [explicit_high_risk_intent_absent_item_and_limited_witnesses](tests/test_player_api.py#L230) |
| F04 | 多人争用同一预算池 | 已实测 | 两个部门在同一游戏分钟提交请求，争用同一额度及班组。未获全部资源的一方实际修改安排。 [c03_f04_independent_same_minute_department_claims_and_replan](tests/test_cross_system_routes.py#L106) |
| F05 | 三个承诺在一季到期、人物分处不同地点 | 已实测 | 三次承诺、同季到期与实际传话链均在同一可回放存档内检查，各跳有已送来源与受众。 [c06_f05_three_promises_and_three_person_echo](tests/test_cross_system_routes.py#L162) |
| F06 | 记事本留在办公室，访问需真实接触 | 已实测 | 实体本的异地获取、原件销毁、已取得的独立副本与调查边界在真实提交路径验证。 [c07_f06_removed_original_persists_as_independent_copy](tests/test_cross_system_routes.py#L188) |
| F07 | 核心人物调离，部分盟友未获消息 | 已实测 | 核心角色先正式调任，旧联系渠道和盟友利益随后按收到的材料变化。 [c04_f07_old_channel_transfers_then_allied_interests_change](tests/test_cross_system_routes.py#L127) |
| F08 | 部分证据与未证实线索并存 | 已实测 | 12 季后依法取得具体记录，调查中的部分知识与正式个人结论保留事件引用；可回放并恢复。 [c09_f08_twelve_seasons_then_independent_acquisition_and_final_finding](tests/test_cross_system_routes.py#L201) |

## 十条原集成链

| 编号 | 要求 | 状态 | 运行证据及边界 |
|---|---|---|---|
| C01 | 跳过汇报、补救后进入资源冲突 | 已实测 | 真实三周工程延期，负责人和上级的既有认知不同；跳过汇报后的自主补救在后来资源请求里有来源。 [c01_f01_skip_real_three_week_delay_then_resource_conflict](tests/test_cross_system_routes.py#L52) |
| C02 | 私下请求、会面或拒绝与知情者变化 | 已实测 | 普通解析及命令测试私下请求、同意/被拒、未发生时保持未知、披露后相关人知情。 [c02_private_meeting_parser_and_disclosed_or_refused](tests/test_cross_system_routes.py#L76) |
| C03 | 两部门请求、仲裁后调整计划 | 已实测 | 两个部门在同一游戏分钟提交请求，争用同一额度及班组。未获全部资源的一方实际修改安排。 [c03_f04_independent_same_minute_department_claims_and_replan](tests/test_cross_system_routes.py#L106) |
| C04 | 领导调任后利益与支持变化 | 已实测 | 核心角色先正式调任，旧联系渠道和盟友利益随后按收到的材料变化。 [c04_f07_old_channel_transfers_then_allied_interests_change](tests/test_cross_system_routes.py#L127) |
| C05 | 旧版保留，调查员取得新版 | 已实测 | 修订后作者和有权核查者取得新版本，玩家仍只持原报告，独立导出与回放保持。 [c05_f02_author_and_auditor_hold_new_version_player_keeps_old](tests/test_cross_system_routes.py#L145) |
| C06 | 传闻经多名人物返回玩家 | 已实测 | 三次承诺、同季到期与实际传话链均在同一可回放存档内检查，各跳有已送来源与受众。 [c06_f05_three_promises_and_three_person_echo](tests/test_cross_system_routes.py#L162) |
| C07 | 销毁原本而副本保留且不自动认定 | 已实测 | 实体本的异地获取、原件销毁、已取得的独立副本与调查边界在真实提交路径验证。 [c07_f06_removed_original_persists_as_independent_copy](tests/test_cross_system_routes.py#L188) |
| C08 | 理智确认后再验高风险行动 | 已实测 | 实际玩家接口覆盖无物品的确认、取消和拒绝后的有限在场观察，禁止补造物品或无源后果。 [explicit_high_risk_intent_absent_item_and_limited_witnesses](tests/test_player_api.py#L230) |
| C09 | 十多季度后取得线索进入终章 | 已实测 | 12 季后依法取得具体记录，调查中的部分知识与正式个人结论保留事件引用；可回放并恢复。 [c09_f08_twelve_seasons_then_independent_acquisition_and_final_finding](tests/test_cross_system_routes.py#L201) |
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
| NEW-03 | 重核后旧确认令牌不能提交 | 已实测 | 同版本连续重核两次。最初两个令牌均被拒，最新令牌只能提交一次，重试命中原回执。 [review_rotates_only_the_current_major_proposal](tests/test_player_api.py#L359) |
| NEW-04 | 纯 Resolver 同快照逐字段相同 | 已实测 | 相同快照执行真实跨季 Resolver 两次，守卫禁止文件/数据库/网络、系统钟、外部进程与随机熵，并逐项比较状态和事件。 [v4_t11_resolver_tape_is_pure_under_io_clock_and_entropy_guards](tests/test_balance_crosscuts.py#L38) |
| NEW-05 | NPC 可基于过时资源认知行动 | 已实测 | 部门基于已收到的班组公告申请。审批时空额已被占用，申请人收到仅涉及自身缺额的回执；对照组先收到后发公告，转入候补。 [stale_crew_notice_allows_request_and_limits_failure_feedback](tests/test_world_disclosures.py#L46) |
| NEW-06 | 失败依赖被阻断，独立动作仍可执行 | 已实测 | 两项同名冲突和两个不同依赖均有逐子动作结果。 [batch_partial_execution_and_causal_dependency](tests/test_player_api.py#L158) |
| NEW-07 | Outbox 领取后崩溃可重新领 | 已实测 | 实际 SQLite 通知 Outbox 经领单未执行、过租期再领、已执行未 ACK 及重复确认；给公开 feed 的版本只出现一次。人物收件在世界事务内单次记账。 [delivery_after_worker_crash_and_expired_lease](tests/test_delivery_recovery.py#L8) |
| NEW-08 | 效果提交与 ack 之间崩溃不重复送达 | 已实测 | 实际 SQLite 通知 Outbox 经领单未执行、过租期再领、已执行未 ACK 及重复确认；给公开 feed 的版本只出现一次。人物收件在世界事务内单次记账。 [delivery_after_worker_crash_and_expired_lease](tests/test_delivery_recovery.py#L8) |
| NEW-09 | 较早截止打断长推进 | 已实测 | 听证等关键节点暂停，未回应不能继续。 [v4_t19_t22_opportunity_and_pause](tests/test_engine_v4.py#L255) |
| NEW-10 | 迟到叙事不能覆盖新界面 | 已实测 | 浏览器延迟返回旧回顾。在回复抵达前推进世界，旧版本和旧世界的文字无法重新打开或覆盖新画面。 [发行包浏览器测试](frontend/tests/browser.test.mjs) |
| NEW-11 | 本人异地无法向原笔记本写入 | 已实测 | 离开办公桌后可见投影无原文，动作需实际取回。 [notebook_private_and_clocked_exposure](tests/test_world_v4.py#L129) |
| NEW-12 | 同处一地不等于读过笔记 | 已实测 | 配偶在场和发现本子均不足以读到文字。收回重放会清除前次接触，第二次发现并读完才获得该条笔记。 [spouse_requires_continuous_access_to_read_notebook](tests/test_world_disclosures.py#L27) |
| NEW-13 | 未经见证的原件销毁不自动定罪 | 已实测 | 私下毁掉原件不生成认定，已经有合法取得链的独立副本仍可留存；他人获知取决于接触来源。 [sc08_same_note_is_private_read_or_preserved_by_different_actions](tests/test_scenario_routes_v4.py#L153) |
| NEW-14 | 导师建议按自己取得的材料 | 已实测 | 同一导师依真实消息说出过时建议或已更新的信息，普通会面中可追到其认知变化。 [sc07_mentor_routes_correct_dated_information_and_interest](tests/test_scenario_routes_v4.py#L138) |
| NEW-15 | 向导师实际出示一条笔记 | 已实测 | 当面向一位导师出示选定条目。披露和收悉事件绑定该条目来源，其他条目与未在场导师的认知保持隔离。 [only_selected_entry_disclosed_to_present_mentor](tests/test_world_disclosures.py#L6) |
| NEW-16 | 安全窗边正常休息 | 已实测 | 干燥窗边不触发环境判定。积水信号先见于开局时间线，改在普通座位休息无环境事件，选择该窗边才暴露，报修后隐患解除。 [safe_seat_skips_accident_and_alert_precedes_exposure](tests/test_world_disclosures.py#L78) |
| NEW-17 | 危险窗边既存环境与可感信号 | 已实测 | 干燥窗边不触发环境判定。积水信号先见于开局时间线，改在普通座位休息无环境事件，选择该窗边才暴露，报修后隐患解除。 [safe_seat_skips_accident_and_alert_precedes_exposure](tests/test_world_disclosures.py#L78) |
| NEW-18 | 阻断外网后核心游戏完整 | 已实测 | 阻断 socket 外连，五个锚点真实走遍九地点、三项目验收开放、导师、实体本、12 季、主动离开及异库恢复。配置不可达提供方的配对世界与离线世界逐步相同。 [v4_t31_all_scenes_projects_mentors_and_ending_with_network_blocked](tests/test_balance_crosscuts.py#L167) |
| NEW-19 | 否定和歧义不能偷偷变动作 | 已实测 | 无确认的歧义输入不会直接提交。 [visible_parser_does_not_reverse_intent](tests/test_player_api.py#L69) |
| NEW-20 | 旁白不能创造新的 NPC 承诺 | 已实测 | 只在登记的可见选项中选择，伪造候选降级。 [bounded_advisor_transport_and_fallback](tests/test_player_api.py#L75) |
| NEW-21 | WAL 导出或中断不破坏前一备份 | 已实测 | 真实在线备份与替换中断对原备份字节比较。 [disk_full_rolls_back_and_backup_replace_is_atomic](tests/test_engine_v4.py#L324) |
| NEW-22 | 缺快照、旧规则、未来存档 | 部分 | 本产品旧 SQLite 结构先备份、迁移重建 feed，缺快照可回放。规格 V3 实际存档仍缺迁移样本。 [schema_migration_rebuilds_feed_and_protects_original](tests/test_delivery_recovery.py#L47) |
| NEW-23 | 从旧点创建独立分支 | 已实测 | 继承不可变历史，父世界维持原进度，旧档重复导入不生成重复分支。 [integrity_branch_replay_and_wal_backup](tests/test_engine_v4.py#L287) |
| NEW-24 | 八起点和八终局由普通行动可达 | 已实测 | 8 个起点分别经普通命令到达 8 类终局，共 64 条。终局引用均能在轨迹中查到。读取终局前一刻的快照重走最后一步，状态和新事件逐项相同。 [ending_from_registered_start_and_final_checkpoint](tests/test_ending_routes.py#L54) |
| NEW-25 | 24 人物、16 案件、32 机制 | 已实测 | 将登记项目和主管替换为 P90、N90。常规办理先因未会签受阻，补齐后按同一资金和班组规则施工、验收、批准并转入二期。24 人、16 案、32 机制另见清单和各机制回归。 [substituted_project_and_owner_from_registration_through_next_phase](tests/test_project_substitution.py#L12) |
| NEW-26 | 十二季档案后继续生涯 | 已实测 | 100 局到达第十三季开头，长局继续至有效退休。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| NEW-27 | 120 季度边界 | 已实测 | 年轻角色走满 120 季、回放一致并继续至自然退休。 [连续参数与生涯实测](BALANCE_CALIBRATION_REPORT.md) |
| NEW-28 | 源码、浏览器、Mac、真实模型分别记录 | 已实测 | 源码、包内浏览器、原生窗口和在线模型的实测状态分别记录。本机模型服务与四种角色的真实响应另列实测，云端模型及真人另行记录。 [发行包浏览器测试](frontend/tests/browser.test.mjs) |
| NEW-29 | 发行包无真实 Inspector 接口 | 已实测 | 在实际包建立生涯，已认证玩家直接请求独立 Inspector、世界内 Inspector 和接口说明，均收到 404 和固定错误正文。 [发行包浏览器测试](frontend/tests/browser.test.mjs) |
| NEW-30 | 文书提示词和玩家文字不产生系统权限 | 已实测 | 要求自己获得审批权的文字只作为私人笔记保存，角色权限、财政、文书均不变。模型虚构十年前的收礼记录时，旁白回退，导出历史保持原样。 [player_words_and_model_invention_have_no_world_authority](tests/test_player_text_boundaries.py#L10) |
| NEW-31 | 中文 IME、键盘与字号 | 部分 | 浏览器覆盖中文组合输入、字号和键盘控件。原生辅助功能树和激活已实测，系统中文输入法实际选词、真人 VoiceOver 操作待验。 [发行包浏览器测试](frontend/tests/browser.test.mjs) |
| NEW-32 | 未知类型、坏 ID、缺模板 | 已实测 | 构建前核对内容清单。九项故障注入覆盖未知准入模式和终局类型、悬空引用、方案额度、办理文案、开局通路唯一性、错误标识及缺失场景模板。未知事件与非法事件载荷另见 T11。 [测试文件](tests/test_content_validation.py) |

## 判定与事件模块

| 编号 | 要求 | 状态 | 运行证据及边界 |
|---|---|---|---|
| J1 | J1 意图归一化与动作依赖 | 已实测 | 21 组输入覆盖复合动作、否定、指代、遗漏和明确依赖。逐段校验原始文本位置，未确认不改世界，部分失败会阻断依赖。 [j1_compound_negation_reference_and_condition_matrix](tests/test_player_api.py#L385) |
| J2 | J2 硬约束 | 部分 | 授权、物品、地点、日程和程序都有实际约束；原验证器注册与全矩阵待核。 [role_grant_lease_and_reject_forgery](tests/test_world_v4.py#L149) |
| J3 | J3 资源仲裁 | 部分 | 同一分钟三个申请人争用同一有限班组与额度，获配和改排均有来源，重试不重复分配。岗位及文书争用的完整排序矩阵仍待复核。 [c03_f04_independent_same_minute_department_claims_and_replan](tests/test_cross_system_routes.py#L106) |
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
| E7 | E7 通信和认知更新 | 已实测 | 消息绑定渠道时延、逐跳来源和内容，受众仅在送达后纳入本人信念。 [c06_f05_three_promises_and_three_person_echo](tests/test_cross_system_routes.py#L162) |
| E8 | E8 八个机制族 | 部分 | 八族共 32 机制有真实正反例，项目和主管替换后批准、开放与二期仍能运行。其余机制族尚未逐一以替换登记的方式验证。 [substituted_project_and_owner_from_registration_through_next_phase](tests/test_project_substitution.py#L12) |
| E9 | E9 事务、恢复与审计 | 已实测 | 领单崩溃、重领、应用后未 ACK、去重并恢复，对照 Inspector 与回放。 [delivery_after_worker_crash_and_expired_lease](tests/test_delivery_recovery.py#L8) |
| E10 | E10 循环诊断与隔离 | 已实测 | 同刻派生循环受控并保留隔离任务，Inspector 可见诊断。 [scheduler_contains_same_minute_cycles_and_keeps_task](tests/test_player_api.py#L127) |

## 起点与终局的实测路径

表中“✓”表示从该正式起点走过完整命令序列。END01 至 END06 使用 `classic` 种子，END07 和 END08 使用 `19`。同一行中的各格使用独立新局。这些路径证明可达性，实际游玩会随材料、承诺、任期与既有健康状况变化。本地测试会从每条路径结尾之前的快照再执行最后一步，对照事件和状态。[64 条路径与局部夹具](tests/test_ending_routes.py)

| 起点 | 退休 | 主动离开 | 长期边缘化 | 调离 | 处分退出 | 调查终章 | 健康或照护退出 | 死亡 |
|---|---|---|---|---|---|---|---|---|
| S01 基层办事经历 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| S02 乡镇执行经历 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| S03 专业技术转任 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| S04 项目协调履历 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| S05 异地交流任职 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| S06 本地长期任职 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| S07 上级机关下派 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| S08 组织培养通道 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

## 桌面发行与真实参与者

2026-11-18 构建的 Apple Silicon 压缩包为 `局中事-macOS-arm64.zip`，SHA-256 为 `c195cbdd6fcf129406d204984ab11acb808e35a32dde540c7f68d83c539ebd66`。已打包二进制要求 macOS 12.0 或以上，实际验证设备为 macOS 27.2 的 Apple M5 Max（128 GiB）。应用通过本机 ad-hoc 签名校验。依赖版本见 [Python 锁文件](requirements-dev.lock)、[前端锁文件](frontend/pnpm-lock.yaml) 和 [Rust 锁文件](src-tauri/Cargo.lock)。

规格 §15.3 的 `source_verified`、`browser_verified`、`macos_built` 和 `macos_smoke_verified` 分别对应下列源码、浏览器和原生结果。

在本机指定 `JZS_TEST_APP` 为发行包后，完整回归通过 270 项，0 跳过，另有一条测试客户端弃用提示。单独测试源码时，269 项通过，原生并发冷启动试验需传入发行包路径。Chrome 与 WebKit 分别针对包内界面和引擎完成 12 项端到端检查，两组均为 12 通过、0 失败、0 跳过。内容注册表、八起点的 64 条终局路径、100 个种子各十二季和 120 季长局的结果见上表与数值报告。

原生窗口测试使用独立的数据目录。第一次生涯建立并进入办公桌，再次打开应用能继续原进度。八个进程同时冷启动时只有一个窗口和一个引擎，另外七个正常退出。强制结束该窗口进程后引擎也被回收。引擎异常退出后，桌面窗口提供诊断导出和重试。通过原生文件选择器恢复后重开，恢复档由第 1 次提交推进至第 2 次提交（游戏第 240 分钟），原档保持第 1 次提交（第 180 分钟）。

四类真实模型调用使用本机 HTTP 服务运行的 `gpt-oss-120b` 和一个临时新局。解析、人物提案、案件提案、旁白的耗时分别为 3.93、2.72、3.09、6.42 秒。四次响应都通过候选校验，状态与调用前一致，历史可回放。云端模型服务尚未实测。[复核真实模型](scripts/verify_model.py)

原生辅助功能树的控件名称和激活已实际核对，真人 VoiceOver 操作与系统中文输入法选词待验。Apple Developer ID 签名及公证、正式 V3.0/V3.1 旧档迁移、六位真人的轮换任务均无验收结果。该版本以可运行功能候选交付，完整设计门槛的独立证据见 G0–G9。[存档兼容范围](SAVE_COMPATIBILITY.md) · [真人试玩安排](PLAYTEST_REPORT.md)
