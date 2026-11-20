# 局中事

《局中事》是一款可离线游玩的中文单人游戏。主菜单有两个入口。

- **生涯模式**。从八种任职经历中选一项进入澄川县，处理工程、人事和家庭事务，或打开原有角色继续游玩。「市井家书」也从这里进入，以普通人的视角串起十一段历史。
- **历史主角模式**。从戊戌变法到新世纪，共有 25 个实名历史事件。按年代筛选，或搜索人物、事件和地点，点选后即可开局。可以扮演沈钧儒、张学良、王晶垚、邓小平、尚爱云等当事人。存档名可以留空，游戏会采用事件名称。

在「历史主角模式」搜索人物或年份，就能从想玩的那天开始。

- **1948，上海，蒋经国。** 一个售票员拿两张车票换了一碗粥。坐下来和他一起吃，你就能试着让车票换饭。等半座城都来吃早饭，粥摊老板娘却想关摊了。
- **1977，北京，邓小平。** 除了恢复笔试，你还可以试办一场实作考试。一个考生修好了收音机，另一个没修响。你肯不肯把修好的那台抱出教室再听一次？
- **1989，北京，邓小平。** 把电视直播交给来访的女工，看看第一个打进来的观众想问谁。一路玩到架空的 1992 年，坐在镜头前回答问题的人也会变。

游戏在「年代与出处」保留真实经过和资料，在章节结束时用「史实对照」与玩家亲历的结局并读。上述电车换饭、实作考试和电视直播均为原创架空路线。在「行记与存档」可回到某次决定前另开分线，保留两段经历。

## 打开游戏

| 电脑 | 打开方式 |
| --- | --- |
| Mac（Apple 芯片） | 双击本地发行目录中的 **局中事.app**。拷贝到另一台 Mac 时，传输 `局中事-macOS-arm64.zip`，解压后打开。 |
| Windows 10／11（x64） | 右键点击 `局中事-Windows-x64.zip`，选择「全部解压缩」，再双击文件夹里的 **局中事.exe**。游戏在默认浏览器打开。游玩时保留启动窗口，结束时点「退出游戏」。 |
| Linux（x86_64、glibc 图形桌面） | 完整解压 `局中事-Linux-x86_64.tar.gz` 到准备长期保留的文件夹，在文件夹中双击 **局中事**。也可以在该目录打开终端，运行 `./局中事`。首次启动会把「局中事」加入应用菜单。 |

三个版本都自带运行游戏所需的组件。Windows 和 Linux 的游戏画面使用本机默认浏览器，可以离线游玩。Linux 退出时，在应用菜单的「局中事」上选择「退出局中事」，或在解压目录运行 `./局中事 --stop`。

选择「生涯模式」中的「建立生涯」，选一项任职经历，确认称谓后进入办公室。第一次可从「档案」对照南渠简报和前次摘录，再到「行动」决定亲自核实、委托或暂缓。选择「日程」推进到已安排的事项。

办公桌和行动页会显示你所在的场所。想听翻纸、材料送达和抵达地点的声音，可以点击游戏时钟旁的「音效」，在「设置」中调节音量。首次游玩默认静音。

在「行动」里可以写「暂缓答复，然后委托核查」。如果第二项必须等第一项受理，写「暂缓答复受理后再委托核查」。提交前会列出每项代价和先后条件。

每次提交都会自动保存。返回主菜单可继续之前的角色。设置中的「真实性—可玩性平衡」支持小数，开局时即生效，中途更改会在 240 个游戏分钟内平滑过渡。已预约或已开始的办理保留原定时点。

换电脑时，在游戏内导出 JSON 存档。县域档从新电脑的「生涯模式」导入；人物长篇在对应目录中选择「导入长篇存档」。存档文件包含完整模拟历史，三个平台共用同一格式。Mac 默认保存在 `~/Library/Application Support/局中事/`；Windows 在 `%LOCALAPPDATA%\局中事`；Linux 在 `~/.local/share/juzhongshi/`，也支持 `XDG_DATA_HOME`。曾用旧源码版在 Linux 建档的玩家会优先看到原有生涯，除非新位置已有存档。

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

澄川县采用架空地名、机构和角色。模型参数是游戏设计值。历史主角各章另有按事件整理的史料与日期。
