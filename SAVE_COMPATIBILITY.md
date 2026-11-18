# 生涯存档与恢复

本版本使用 SQLite schema 1、JSON 导出格式 `juzhongshi-save/1`。每份导出含完整创世状态、不可改写的事件与状态差量、已提交命令及收据。参数包、计算版本、领域内容包和世界版本随档保存。

- 进入生涯或读取界面不会推进游戏时钟。正常退出后可以从同一世界恢复未完成工作、消息、软窗口、时钟阈值和未结束的取向过渡。
- 导入先校验格式、资源包、历史链、每笔状态摘要、序号与领域约束，再在一个事务里安装。校验失败保留当前档案。重复导入相同版本维持同一世界。导入本机已存在世界的另一版会建立独立分支。
- 分支保留来源世界与分叉版本。分叉以前的事件字节保留；分叉以后的命令、事件编号和随机流独立。已封存的任务、接触链和机会阈值保持原值。
- 普通游戏视图只展示已经送达的记录。完整 JSON 导出是可以恢复世界的本地备份，含尚未公开的领域状态。SHA-256 用来识别损坏与版本冲突。该格式没有数字签名。
- SQLite 使用 WAL。手工转移时可用界面导出，或调用 `GameStore.backup(destination)` 在线生成一致的 SQLite 副本。备份用临时文件校验后替换目标。
- 原仓库 v2 演示的 `world_state/event_log/outbox` 与本版没有共同的创世、规则包或长期内容合同。新引擎会拒绝直接覆盖这类数据库。尚无可验证的 V3.0/V3.1 真实存档样本，旧动作绑定与时钟的完整迁移仍待验证。
- 为诊断损坏，`GameStore.replay(world_id)` 从事件效果重建当前状态并比较持久化投影。回放不会调用角色、模型或推进调度器。每 32 个版本的快照缩短历史分支/重试的读取路径。快照不存在或快照摘要不一致时从事件链重建。

可重复检查命令为 `.venv/bin/python -m pytest -q tests/test_engine_v4.py`。

## 开发者只读检查

`scripts/inspect_game.py` 使用导出的 JSON 或 SQLite 的在线备份建立临时隔离副本。默认生成一份示例生涯。开发者可以通过 `worlds`、`view`、`actor`、`chain`、`queue`、`quarantine` 检查完整的历史快照。此工具独立于玩家 API 和发行包。

```sh
.venv/bin/python scripts/inspect_game.py chain --save career.json --limit 5
.venv/bin/python scripts/inspect_game.py actor --save career.json --actor N09 --revision 3
.venv/bin/python scripts/inspect_game.py queue --db career.sqlite3 --world WORLD_ID
```

## SQLite 的通知队列迁移

数据库结构 1 首次由结构 2 打开时，程序通过 SQLite 在线备份 API 生成同目录的 `.schema1-backup.sqlite3` 副本，再在一个事务内建立可见消息投递表并从原事件按版本回填。失败时回滚，原始事件字节保留。重复启动读取已完成的版本标记。游戏 JSON 导出不依赖运行时的订阅者或租约。回归命令为 `python -m pytest -q tests/test_delivery_recovery.py`。
