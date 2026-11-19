# 美术和第三方组件

| 文件 | 来源与使用 |
| --- | --- |
| `frontend/public/county-office.jpg` | 为虚构的澄川县办公室制作的主菜单画面，随游戏离线提供。 |
| `frontend/public/county-locations.jpg` | 为本作制作的九个虚构场所场景图集。地点选择与准入规则由游戏状态决定。 |
| `frontend/public/scenes/office.webp`、`canal.webp`、`home.webp` | 为本作绘制的办公室、南渠便道和家庭餐桌。插图按玩家已到达的地点展示。工程量、进度和调查结果由玩家取得的材料说明。 |
| `frontend/public/seal.svg` | 游戏界面的「局」字标识。 |
| `frontend/src/sound.ts` | 翻纸、案卷落桌和脚步均由游戏在本机短时合成，可在游玩时开关和调节音量。 |
| `frontend/public/game-icon.png`、`src-tauri/icons/game.icns`、`src-tauri/icons/icon.png` | 应用图标「窗内留灯」。深蓝色办公室窗框内亮着一盏台灯。 |
| `frontend/public/chronicle/*.webp` | 为长篇创作的年代情境插画。人物篇以环境和实物标识事件，画面标有「年代情境插画」。 |
| `frontend/public/chronicle/*.mp3` | 从本作原创声音样带制作的三段短配乐，分别用于受挫、取得材料和局势转折。按已提交的选择触发，沿用音效开关与音量设置。 |
| 字体 | 使用系统自带中文字体，新局与存档不依赖网络字体。 |
| 运行时和开发依赖 | Python、JavaScript、Rust 版本分别见 requirements-dev.lock、frontend/pnpm-lock.yaml、src-tauri/Cargo.lock。macOS 包的 Contents/Resources/THIRD_PARTY_NOTICES.txt 列出构建所用组件和上游许可。 |

虚构世界的规则和规模依据用户提供的 V4.0 连续参数规格。原仓库没有明示项目整体的开放许可，本次改动沿用仓库现有权属安排。
