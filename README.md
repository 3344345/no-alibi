# 局中事

在虚构的江岚省临江市澄川县，你接手一份南渠进度简报。可以把附件交给联络员核对，亲自去现场，也可以先交一份限定范围的意见。工程是否开放，要看技术员实际检查、主管批准和施工方移交。

《局中事》是本地单人中文生涯模拟游戏。八种起点使用同一个世界。日程、文件版本、证据流转、家庭安排、岗位变化和项目预算随你推进的游戏时间运行。读材料时，时钟停在原处。

## 在 Mac 上开始

打开本地发行目录中的 **局中事.app**，选择「建立生涯」，选一项任职经历，确认称谓后进入办公室。第一次可从「档案」对照南渠简报和前次摘录，再到「行动」决定亲自核实、委托或暂缓。选择「日程」推进到已安排的事项。

每次提交都会自动保存。返回主菜单可继续之前的角色。设置中的「真实性—可玩性平衡」支持小数，开局时即生效，中途更改会在 240 个游戏分钟内平滑过渡。已预约或已开始的办理保留原定时点。

游戏的默认数据目录是当前用户的 `~/Library/Application Support/局中事/`。搬到另一台 Mac 时，在游戏内导出 JSON 存档，再由对方设备的主菜单导入。存档文件包含完整模拟历史，适合自己备份和迁移。

## 从源码运行

在 Apple Silicon Mac 上使用 Python 3.12、Node.js 22 或以上、pnpm 和 Rust。首次安装依赖需要网络。完成安装和构建后，本地游戏可以离线运行。

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock
(cd frontend && pnpm install --frozen-lockfile && pnpm build)
.venv/bin/python main.py
```

默认打开浏览器。开发时可用 `--no-browser` 获取本次本机入口，用 `--data-dir` 指定独立测试目录。Mac 桌面壳和浏览器均使用同一套 FastAPI 接口、Svelte 界面和 SQLite 世界数据。正式桌面包自带运行时。

```sh
scripts/build_macos.sh
.venv/bin/python -m pytest -q
.venv/bin/python scripts/content_manifest.py --check
.venv/bin/python scripts/calibrate.py --json /tmp/jzs-calibration.json
(cd frontend && pnpm check && pnpm test:e2e)
```

macOS 打包还需要 Xcode Command Line Tools。输出为 `release/局中事.app`、压缩包和 SHA-256 清单。这个版本使用本机临时签名。浏览器测试需要可用的 Chrome 或 Playwright WebKit。

## 可选语言服务

默认采用本地按钮、受限自由输入和带来源的叙述。需要使用外部语言模型时，由玩家在启动服务的环境中同时提供 `JUZHONGSHI_AI_URL`（完整的兼容 chat/completions 请求地址）和 `JUZHONGSHI_AI_MODEL`。需要身份验证的提供商还可读取 `JUZHONGSHI_AI_KEY`。这些值只供服务进程使用。

配置后，语言服务可协助解释玩家输入、选择一个角色已知的合格陈述、选择已触发事项的跟进方式，或从玩家已看到的条目中选取回顾。候选须通过本地校验；连接超时、未知编号或不合规输出会回到本地规则。

## 交付与核验

- [实现范围与发布状态](IMPLEMENTATION_STATUS.md)
- [验收记录](ACCEPTANCE_REPORT.md) 与 [逐条需求追踪](REQUIREMENTS_TRACEABILITY.csv)
- [内容目录](CONTENT_MANIFEST.json) 与 [连续参数实测](BALANCE_CALIBRATION_REPORT.md)
- [存档兼容与恢复](SAVE_COMPATIBILITY.md) 与 [真人试玩记录](PLAYTEST_REPORT.md)

本作采用架空地名、机构和角色。模型参数是游戏设计值。
