# 《局中事》开发断点

2026-11-18 15:54（上海）。用户要求停止并于下次续作。当前工作保存在本地分支 `game-v4`，远端基线是 `b89aebc31fe44cd6264cd5a28fd0d7733a3fd5d6`。用户已确认最终代码推至该仓库的新分支，同时保留本地 Mac 版；暂停时尚未推送。继续时先读取本文件和本地分支 HEAD。用户另有当可读账户额度剩余 1% 或以下时保存并暂停的要求。

## 已保留的成果

- 可运行游戏源代码、Svelte 玩家界面、FastAPI 和 SQLite 引擎、连续参数、分支与回放、离线内容、Apple Silicon 桌面壳、打包脚本、依赖锁和测试均在本分支。
- 15:40 的构建位于 `release/局中事.app` 和 `release/局中事-macOS-arm64.zip`。压缩包 SHA-256 为 `6d4dbba6bb2a1b67dd74f3f468437edfce419707f4f071a8793b9ceec8733d4b`。应用通过本机 ad-hoc 签名校验。包内引擎和包内界面在 Chrome、WebKit 各通过九条浏览器旅程。该构建早于本断点的最新源码。构建和浏览器日志在本机 `.artifacts/checkpoint/`。
- 实测已覆盖 100 种子 × 12 季度、120 季度长局与退休、八种结局、四类报告事实包、六人物线以及跨季度案卷。最新十场景与 32 机制专项测试已单独通过，见 tests/test_scenario_routes_v4.py、tests/test_mechanism_contracts_v4.py。验收文档仍需按最终代码同步。
- 严格 PlayerView、重大行动绑定确认、批量命令、到场观察、按角色过滤的可选模型候选、可恢复的消息投递、分页可见历史均已接入。真实模型、真人试玩、真实 V3 存档迁移各自保留待验。
- 本轮测试窗口、本地游戏服务及测试浏览器已经关闭。开发环境与本地构建保留。临时 GitHub 认证辅助文件已清理。

## 从这里继续

1. 先修复 `tests/test_world_disclosures.py::test_safe_seat_skips_accident_and_alert_precedes_exposure`。测试在 `damp.log` 查找创世时的积水提示，而 `Play.__init__` 将该列表初始化为空；创世提示已计入初始世界时间线。核对生成记录，再修正测试取证位置。同时清理 `game/world_disclosure.py` 的未使用局部变量。最近一次相关组合测试为 18 通过、1 失败。
2. 重跑完整 pytest、内容清单、100 种子校准与前端检查。复核真实待办和历史来源索引，更新 ACCEPTANCE_REPORT.md 末节与 REQUIREMENTS_TRACEABILITY.csv。下次应补验最终原生窗口的异常退出/重开、双实例与恢复的实际结果；浏览器的九条旅程另行计数。
3. 用最后一次源代码重新构建，再以 `JZS_TEST_APP` 指向实际生成的 .app，在 Chrome 和 WebKit 中各跑一次前端端到端测试。校验压缩包和应用签名。为数据安全，使用独立测试档案目录。
4. 核对本地代码和产物后推送 `game-v4`，核验远端提交与本地一致。截图含已公开展示的令牌，续作时优先使用用户配置的 GitHub 登录；保持令牌、会话地址与私人存档在代码和日志以外。

本机 Python 虚拟环境在 `.venv`。前端用 pnpm，构建步骤见 README。此轮临时 Rust 工具链在 `/tmp/jzs-build-tools/`，临时目录若被系统清理可按标准 Rust 工具链重建。项目使用 Apple Silicon，不依赖科研项目目录。
