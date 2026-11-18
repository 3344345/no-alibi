# 局中事

在虚构的江岚省临江市澄川县，你接手一份南渠进度简报。可以把附件交给联络员核对，亲自去现场，也可以先交一份限定范围的意见。工程是否开放，要看技术员实际检查、主管批准和施工方移交。

《局中事》是本地单人中文生涯模拟游戏。八种起点使用同一个世界。日程、文件版本、证据流转、家庭安排、岗位变化和项目预算随你推进的游戏时间运行。读材料时，时钟停在原处。

## 打开游戏

| 电脑 | 打开方式 |
| --- | --- |
| Mac（Apple 芯片） | 双击本地发行目录中的 **局中事.app**。拷贝到另一台 Mac 时，传输 `局中事-macOS-arm64.zip`，解压后打开。 |
| Windows 10／11（x64） | 右键点击 `局中事-Windows-x64.zip`，选择「全部解压缩」，再双击文件夹里的 **局中事.exe**。游戏在默认浏览器打开。游玩时保留启动窗口，结束时点「退出游戏」。 |
| Linux（x86_64、glibc 图形桌面） | 完整解压 `局中事-Linux-x86_64.tar.gz` 到准备长期保留的文件夹，在文件夹中双击 **局中事**。也可以在该目录打开终端，运行 `./局中事`。首次启动会把「局中事」加入应用菜单。 |

三个版本都自带运行游戏所需的组件。Windows 和 Linux 的游戏画面使用本机默认浏览器，可以离线游玩。Linux 退出时，在应用菜单的「局中事」上选择「退出局中事」，或在解压目录运行 `./局中事 --stop`。

选择「建立生涯」，选一项任职经历，确认称谓后进入办公室。第一次可从「档案」对照南渠简报和前次摘录，再到「行动」决定亲自核实、委托或暂缓。选择「日程」推进到已安排的事项。

在「行动」里可以写「暂缓答复，然后委托核查」。如果第二项必须等第一项受理，写「暂缓答复受理后再委托核查」。提交前会列出每项代价和先后条件。

每次提交都会自动保存。返回主菜单可继续之前的角色。设置中的「真实性—可玩性平衡」支持小数，开局时即生效，中途更改会在 240 个游戏分钟内平滑过渡。已预约或已开始的办理保留原定时点。

换电脑时，在游戏内导出 JSON 存档，再从新电脑的游戏主菜单导入。存档文件包含完整模拟历史，三个平台共用同一格式。Mac 默认保存在 `~/Library/Application Support/局中事/`；Windows 在 `%LOCALAPPDATA%\局中事`；Linux 在 `~/.local/share/juzhongshi/`，也支持 `XDG_DATA_HOME`。曾用旧源码版在 Linux 建档的玩家会优先看到原有生涯，除非新位置已有存档。

## 从源码运行

源码版使用 Python 3.12、Node.js 22 或以上和 pnpm。下列命令适用于 macOS 与 Linux。首次安装依赖需要网络。完成安装和构建后，本地游戏可以离线运行。

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock
(cd frontend && pnpm install --frozen-lockfile && pnpm build)
.venv/bin/python main.py
```

在 Windows PowerShell 可执行以下命令启动同一源码版。

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Push-Location frontend
pnpm install --frozen-lockfile
pnpm build
Pop-Location
.\.venv\Scripts\python.exe main.py
```

默认打开浏览器。开发时可用 `--no-browser` 获取本次本机入口，用 `--data-dir` 指定独立测试目录。Mac 桌面壳和浏览器均使用同一套 FastAPI 接口、Svelte 界面和 SQLite 世界数据。正式桌面包自带运行时。

```sh
.venv/bin/python -m pytest -q
.venv/bin/python scripts/content_manifest.py --check
.venv/bin/python scripts/calibrate.py --json /tmp/jzs-calibration.json
(cd frontend && pnpm check && pnpm test:e2e)
```

浏览器测试使用 Chrome 或 Playwright WebKit。

## 从源码构建发行包

在仓库根目录运行相应命令。首次构建需要联网获取锁定的依赖，成品位于 `release/`。

| 构建机 | 命令 | 构建准备 |
| --- | --- | --- |
| Apple Silicon Mac | `scripts/build_macos.sh` | 按上节安装开发依赖并构建前端，另需 Xcode Command Line Tools 和 Rust 1.89 或以上。脚本生成本机临时签名的应用与 ZIP。可用 `PYTHON` 指定虚拟环境的解释器。 |
| Windows x64 | `py -3.12 scripts/build_windows.py` | 需要带 pip 的 Python、Node.js、pnpm 及系统 .NET Framework 的 64 位 C# 编译器。脚本构建前端和图形启动器，并将锁定的 Windows Python 运行时、游戏及界面写入 ZIP。 |
| Linux x86_64 | `.venv/bin/python scripts/build_linux.py` | 按上节构建前端，准备 Python 3.12 或以上、pip 和 `cc`。脚本生成内含 x86_64 运行时与桌面入口的 tar.gz。 |

发行包的核验值与已测环境见[发行状态](IMPLEMENTATION_STATUS.md)。

## 可选语言服务

默认采用本地按钮、受限自由输入和带来源的叙述。需要使用外部语言模型时，由玩家在启动服务的环境中同时提供 `JUZHONGSHI_AI_URL`（完整的兼容 chat/completions 请求地址）和 `JUZHONGSHI_AI_MODEL`。需要身份验证的提供商还可读取 `JUZHONGSHI_AI_KEY`。这些值只供服务进程使用。

配置后，语言服务可协助解释玩家输入、选择一个角色已知的合格陈述、选择已触发事项的跟进方式，或从玩家已看到的条目中选取回顾。候选须通过本地校验。单次连接等待上限为 12 秒。连接超时、未知编号或不合规输出会回到本地规则，本次推进的后续候选也由本地处理。

配置好服务后，可运行 `.venv/bin/python scripts/verify_model.py`。脚本用独立测试生涯核对四种职责及回放，退出时清理测试存档。

## 交付与核验

- [实现范围与发布状态](IMPLEMENTATION_STATUS.md)
- [验收记录](ACCEPTANCE_REPORT.md) 与 [逐条需求追踪](REQUIREMENTS_TRACEABILITY.csv)
- [内容目录](CONTENT_MANIFEST.json) 与 [连续参数实测](BALANCE_CALIBRATION_REPORT.md)
- [存档兼容与恢复](SAVE_COMPATIBILITY.md) 与 [真人试玩记录](PLAYTEST_REPORT.md)

本作采用架空地名、机构和角色。模型参数是游戏设计值。
