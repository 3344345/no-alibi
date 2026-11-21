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
| `shanghai_tram.webp`、`beijing_live.webp` | 为架空剧情创作的两幅人物场景。上海粥摊和电车售票员、北京演播室和上镜女工均为虚构。 |
| `frontend/public/chronicle/*.mp3` | 从本作原创声音样带制作的三段短配乐，分别用于受挫、取得材料和局势转折。按已提交的选择触发，沿用音效开关与音量设置。 |
| `frontend/public/chronicle/sound/*.mp3` | 由 `scripts/score_chronicle.py` 为本作编曲和合成。三首循环配乐与房间、院落、接线台、车站、放映机五条立体声环境轨交叉淡入。另有乔素琴家宴的一段手风琴舞曲，随玩家的广播决定播放。 |
| 长篇场景图 | 16 幅为本作制作的原创情境画面，分布于 `frontend/public/chronicle/` 和 `frontend/public/scenes/`。北京的接线间与院落放映、山西塬上的半面池、裁缝铺的三件袖样、上海两代人的家与澄川七路站台均作剧情演出使用。实景史料在主菜单的「年代放映室」单列。 |
| `frontend/public/cinema/` | 北京宫城全景（1901年拍摄）、上海新闻片（馆藏编目1946年）及1984年上海仪表厂现场。馆藏号、片段出处和使用依据可在每段影片的「来源」中查阅。附游戏编写的中文镜头注释。 |
| 字体 | 使用系统自带中文字体，新局与存档不依赖网络字体。 |
| 运行时和开发依赖 | Python、JavaScript、Rust 版本分别见 requirements-dev.lock、frontend/pnpm-lock.yaml、src-tauri/Cargo.lock。macOS 包的 Contents/Resources/THIRD_PARTY_NOTICES.txt 列出构建所用组件和上游许可。 |

虚构世界的规则和规模依据用户提供的 V4.0 连续参数规格。原仓库没有明示项目整体的开放许可，本次改动沿用仓库现有权属安排。

## 年代放映室

- `palace.mp4` 是美国国会图书馆的《The Forbidden City, Pekin》全片。C. Fred Ackerman 于1901年1月31日拍摄，American Mutoscope & Biograph Company 于1903年在美国发行，美国版权登记号 H34805，原片已进入公版。数字拷贝由 Library of Congress, Motion Picture, Broadcasting, and Recorded Sound Division 提供。[馆藏记录](https://www.loc.gov/item/mp76000090/)
- `arrival.mp4` 是1946年 United News 第197卷第一则上海新闻，取馆藏 DVD 转录第00:24至01:31，保留原声。美国国家档案馆馆藏 208-UN-197，NAID 39104，使用限制栏为 Unrestricted。所用 FedFlix 数字拷贝标注 CC0。[馆藏记录](https://catalog.archives.gov/id/39104) · [拷贝与使用说明](https://archive.org/details/gov.archives.arc.39104)
- `factory.mp4` 节选自1984年4月30日白宫电视办公室在上海福克斯波罗公司拍摄的同期录像，第09:20至12:12，带号 F87，NAID 75502096。馆方将 WHTV 系列列为公版，本片取自档案馆 MP4。[原卷记录](https://www.reaganlibrary.gov/archives/video/trip-china-president-reagans-remarks-shanghai-foxboro-company) · [馆方权属说明](https://www.reaganlibrary.gov/archives/audiovisual/white-house-television-office-whtv)
- 三段影片均位于 `frontend/public/cinema/`。选片按钮与海报使用原片内容；可切换的中文镜头注释为本作撰写。

## 镜头阅读与三出新戏

此版的宽幅插画为剧情创作，以戏中人和想象场面为画面主体。喜棚两侧、折椅与旧钢琴、放映间和工作台使用独立画面。县城片中插入的黑白影像亦为本作创作。

- `scripts/score_scene_reel.py` 生成影戏双声部和旧礼堂钢琴配乐、茶盖、竹杆、琴弦、雨点及低音退场声。
- `scripts/score_seven_seconds.py` 合成十二秒双话筒素材，台口、后门和两路合听可离线切换；波形取自相同音轨。
- `scripts/score_shadow_window.py` 和 `scripts/score_aftershow.py` 分别制作皮影锣点和旧影院声效。玩家能在静音时根据文字和画面操作全部新场面。

## 4.6.0 人物演出与剧情短片

人物现场使用独立的眼、眉、唇形、头颈和手臂动作。25 张历史肖像的原始来源、作者、许可及改动载于 `frontend/src/historicalCast.json` 和游戏首页「人物与出处」。档案照片用于确认人物形貌，游戏中的动作、台词及衣着为戏剧演出。相同方式共享的照片及其裁切、动画素材遵循相应原许可。12 张历史角色戏剧定妆另列于 `frontend/src/originalCast.json`。普通演员定妆、场景、服装和手势素材为本项目创作。

49 段原创剧情短片均附本地中文字幕与立体声拟音。家庭、历史与澄川县城的制作脚本见 `scripts/film_family.py`、`scripts/render_witness_films.py` 及 `scripts/render_county_motion.py`。《倒带七秒》将夜间电台、双盘录音机、折椅合拢与琴键剪成 21 秒短片。历史馆藏新闻片保留在原「年代放映室」。
