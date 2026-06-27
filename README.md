# ConferenceBuddy · 会议幻灯片自动总结

> **一句话：把一沓在台下随手拍的、歪斜带眩光的会议幻灯片照片，自动变成一份排版统一、干净专业的总结 PPT。**
>
> **In one line: turn a stack of crooked, glare-covered phone photos of conference slides into a clean, uniformly-formatted summary deck — automatically.**

**当前版本 / Current version: 2.1.x**

---

## ✨ 效果：从一张潦草的照片，到一页成品幻灯片

## ✨ The wow: from a messy photo to a finished slide

🇨🇳 你在台下用手机拍的照片是这样的：上面有一排射灯、左右是蓝色装饰边框、屏幕偏蓝色、下面全是观众后脑勺、整体还歪着、反光。ConferenceBuddy 会**自动识别出中间真正的幻灯片区域 → 裁掉边框/射灯/人头 → 把屏幕翻拍还原成干净的白底"扫描件" → 读懂内容并写成中文要点 → 排进统一模板**。全程不需要你手动抠图或录入。

🇬🇧 A photo you snap from the audience looks rough: spotlights along the top, blue decorative frames on the sides, a blue color cast on the screen, rows of audience heads at the bottom, keystone tilt, and glare. ConferenceBuddy **automatically finds the real slide area → crops away the frames / spotlights / heads → restores the screen photo into a clean white "scanned document" → reads the content and writes Chinese bullet points → lays it into one consistent template** — with no manual cropping or data entry.

![pipeline](assets/pipeline.png)

🇨🇳 上图：① 原始手机照片 → ② 自动识别 PPT 区域（绿框）→ ③ 裁切 → ④ 扫描成白底文档。下图：最终生成的一页成品幻灯片（左边是处理后的幻灯片图，右边是自动写出的中文摘要，底部是固定位置的关键概念栏）。

🇬🇧 Above: ① raw phone photo → ② auto-detected slide region (green box) → ③ crop → ④ scan to a clean document. Below: one finished output slide (processed slide image on the left, auto-written Chinese summary on the right, a fixed-position keyword bar at the bottom).

![final slide](assets/final_slide.png)

> 🔒 **隐私说明 / Privacy note** — 🇨🇳 上面示例照片里所有人脸和观众区域都已做模糊处理；幻灯片内容是公开发表的学术参考文献。🇬🇧 All faces and the audience area in the example photo have been blurred; the slide content shown is publicly-published academic references.

---

## 🧠 它做了什么 / What it does

🇨🇳 你把一个装满会议幻灯片照片的文件夹交给它，它会：

🇬🇧 You point it at a folder of conference slide photos, and it will:

| 步骤 Step | 中文 | English |
|-----------|------|---------|
| 1 | **扫描文件夹**，自动识别 `Focus/`（主讲）+ `Other/`（其他讲者）结构，或把所有照片都当作主讲 | **Scan** the folder, auto-detecting a `Focus/` + `Other/` layout, or treating everything as Focus |
| 2 | **自动裁切**：识别每张照片里真正的 PPT 区域，去掉左右边框、上方射灯、下方观众 | **Auto-crop** each photo to the real slide region — frames, spotlights, audience removed |
| 3 | **扫描还原**：去掉屏幕色偏/眩光，把白底幻灯片还原成干净的"扫描件"质感（深色主题的幻灯片会自动跳过）| **Scan** away the color cast / glare to a clean white "document" look (dark-themed slides are skipped automatically) |
| 4 | **视觉读图**：用 Claude 的视觉能力读懂每张幻灯片，提取标题、关键词、要点（中文）| **Read** each slide with Claude vision — title, keywords, bullet points (in Chinese) |
| 5 | **制式生成**：把所有内容排进一个版式永远一致的 PPT | **Generate** a PPTX with a layout that never drifts page to page |

---

## 🚀 安装与部署 / Installation & Deployment

🇨🇳 ConferenceBuddy 是一个"技能（Skill）"——本质就是一个文件夹，放进 AI 编程助手的技能目录即可。下面给出三种环境的完整步骤。**中国大陆用户建议用腾讯 CodeBuddy（方案 B）**，因为 Claude Code 在国内无法直接使用。

🇬🇧 ConferenceBuddy is a "Skill" — just a folder you drop into your AI coding assistant's skills directory. Three environments are covered below. **Users in mainland China should use Tencent CodeBuddy (Option B)**, since Claude Code is not directly available there.

### 前置依赖 / Prerequisites

```bash
pip install python-pptx Pillow opencv-python numpy
```

🇨🇳 还需要系统里有**宋体**和 **Times New Roman**（Windows 自带）；中文渲染用。
🇬🇧 You also need the **SimSun (宋体)** and **Times New Roman** fonts installed (bundled with Windows) for Chinese rendering.

---

### 方案 A · Claude Code（国际用户）/ Option A · Claude Code (international)

🇨🇳 1) 安装 Claude Code（官方文档：https://claude.com/claude-code ）。2) 把本仓库克隆/下载后，整个 `conference-buddy` 文件夹复制到技能目录：

🇬🇧 1) Install Claude Code (docs: https://claude.com/claude-code). 2) Clone/download this repo and copy the whole `conference-buddy` folder into your skills directory:

```bash
git clone https://github.com/tianmoul/conference-buddy.git
# Windows
xcopy /E /I conference-buddy "%USERPROFILE%\.claude\skills\conference-buddy"
# macOS / Linux
cp -r conference-buddy ~/.claude/skills/
```

🇨🇳 3) 在 Claude Code 里直接说「会议总结 + 照片文件夹路径」即可触发。
🇬🇧 3) In Claude Code, just say "会议总结" / "conference summary" with the photo folder path to trigger it.

---

### 方案 B · 腾讯 CodeBuddy（国内推荐）/ Option B · Tencent CodeBuddy (recommended in China)

🇨🇳 CodeBuddy 是腾讯云推出的 AI 代码助手，其命令行版 **CodeBuddy Code** 与 Claude Code 用法基本一致，并且**支持 Skill**。这是国内用户的首选。

🇬🇧 CodeBuddy is Tencent Cloud's AI coding assistant; its CLI, **CodeBuddy Code**, works much like Claude Code and **supports Skills**. This is the go-to for users in China.

**第 1 步：安装 CodeBuddy Code CLI / Step 1: Install the CLI**

🇨🇳 需要 Node.js 18.20 以上。用 npm 安装：
🇬🇧 Requires Node.js 18.20+. Install via npm:

```bash
npm install -g @tencent-ai/codebuddy-code
```

🇨🇳 或者用免 Node 的原生安装包 / 🇬🇧 Or the Node-free native installer:

```powershell
# Windows (PowerShell)
irm https://www.codebuddy.cn/cli/install.ps1 | iex
```
```bash
# macOS / Linux
curl -fsSL https://www.codebuddy.cn/cli/install.sh | bash
```

🇨🇳 验证安装 / 🇬🇧 Verify:

```bash
codebuddy --version
```

**第 2 步：放入技能目录 / Step 2: Drop the skill into the skills directory**

🇨🇳 CodeBuddy 的技能目录是 `~/.codebuddy/skills/`（Windows 为 `%USERPROFILE%\.codebuddy\skills\`）。把整个 `conference-buddy` 文件夹复制进去：

🇬🇧 CodeBuddy's skills directory is `~/.codebuddy/skills/` (`%USERPROFILE%\.codebuddy\skills\` on Windows). Copy the whole `conference-buddy` folder there:

```bash
git clone https://github.com/tianmoul/conference-buddy.git
# Windows
xcopy /E /I conference-buddy "%USERPROFILE%\.codebuddy\skills\conference-buddy"
# macOS / Linux
cp -r conference-buddy ~/.codebuddy/skills/
```

**第 3 步：使用 / Step 3: Use it**

🇨🇳 启动 `codebuddy`，说「会议总结 D:\照片\某会议」即可。
🇬🇧 Start `codebuddy` and say "会议总结 D:\photos\my-conf" (or "conference summary …").

> 🇨🇳 官方文档 / 🇬🇧 Docs: https://www.codebuddy.ai/docs/zh/cli/installation

---

### 方案 C · WorkBuddy（腾讯职场智能体 App）/ Option C · WorkBuddy (Tencent's office-agent app)

🇨🇳 **WorkBuddy** 是腾讯推出的"职场 AI 智能体"桌面/手机工作台，面向不写代码的普通办公用户：你用一句话描述需求，它像同事一样自主规划并执行。安卓用户可在华为应用市场、小米应用商店、应用宝等搜索「**WorkBuddy**」下载。

🇬🇧 **WorkBuddy** is Tencent's "office AI agent" desktop/mobile workspace for non-coders: describe a task in one sentence and it plans and executes like a colleague. Android users can search "**WorkBuddy**" in Huawei AppGallery, Xiaomi GetApps, or Tencent MyApp to install.

🇨🇳 ⚠️ 说明：WorkBuddy 偏向"终端用户"产品，技能（Skill）的安装与运行目前以 **CodeBuddy Code（方案 B）** 为准。如果你只想要成品 PPT 而不想碰命令行，可以请身边会用 CodeBuddy 的同事按方案 B 跑一次。

🇬🇧 ⚠️ Note: WorkBuddy is the end-user product; installing and running Skills today is done through **CodeBuddy Code (Option B)**. If you just want the finished deck without touching a terminal, ask a colleague who uses CodeBuddy to run Option B once for you.

> 🇨🇳 官网 / 🇬🇧 Site: https://www.codebuddy.cn/work/

---

## 📂 照片库结构 / Photo library layout

```
Library/
└── 2026_06_25_MyConf/
    ├── Focus/          ← 主讲幻灯片（每张照片一页）/ main speaker (one slide per photo)
    │   ├── IMG_001.jpg
    │   └── ...
    └── Other/          ← 其他讲者（每位 3 张代表性照片）/ other speakers (3 photos each)
        └── ...
```

🇨🇳 没有子文件夹也行——根目录里的所有照片都会被当作主讲幻灯片。
🇬🇧 No subfolders is fine — every photo in the root is treated as a Focus slide.

---

## ⚙️ 配置项 / Configuration

🇨🇳 所有参数都在生成脚本顶部，**改一行即可**，下面的渲染代码不用动。

🇬🇧 Every setting lives at the top of the generated script — **change one line**, never touch the rendering code below.

```python
# 字体（中文/英文分别设置）/ Fonts (Chinese / Latin set separately)
FONT_ZH      = '宋体'                 # 中文字体 Chinese typeface
FONT_EN      = 'Times New Roman'      # 英文/数字字体 Latin typeface

# 摘要字号 / Summary font size  —— 关键可调项！
SUMMARY_SIZE = 14   # 右侧摘要正文字号。想看清楚就调大(14/16)；想塞更多文字就调小(11/12)
                    # Right-column summary size. Bigger (14/16) = easier to read;
                    # smaller (11/12) = fits more text. Sub-points auto = SUMMARY_SIZE - 2.
OTHER_SIZE   = 13   # 其他讲者要点字号 / Other-speaker bullet size

# 扫描效果 / Document-scan
SCAN_MODE    = 'auto'   # 'auto' 自动(亮片扫描, 暗片跳过) | 'on' 全扫 | 'off' 关闭
FORCE_NOSCAN = set()    # 强制不扫描的照片编号 / nums to always keep as a plain crop

# 版式 / Layout
LAYOUT = '16:9'         # '16:9' 宽屏(默认) 或 'A4' 横向
```

🇨🇳 **关于字号**：14 号看着清楚，但如果某场会议你想写很多文字摘要，14 号可能太大放不下——这时把 `SUMMARY_SIZE` 调到 11 或 12 即可。
🇬🇧 **About sizes**: 14 pt is comfortable to read, but if you want long text summaries it may be too big — just set `SUMMARY_SIZE` to 11 or 12.

---

## 🗣️ 触发方式 / How to trigger

🇨🇳 在 Claude Code / CodeBuddy 里说出下面任意一句即可：
🇬🇧 Say any of these in Claude Code / CodeBuddy:

```
会议总结 D:\Library\2026_06_25_MyConf
会议报告 这个文件夹的照片
conference summary from this folder
generate conference PPTX from Library/2026_06_25_MyConf
```

🇨🇳 它会先问你会议名称、日期、地点，然后逐张分析照片（每张约 5–10 秒），最后生成 PPT 并告诉你文件路径和页数。

🇬🇧 It will ask for the conference name, date, and venue, then analyze each photo (~5–10 s each), and finally produce the PPTX and report the file path and page count.

---

## 🛠️ 技术原理 / How it works under the hood

🇨🇳 裁切和扫描的核心都在 `slide_crop.py`，用的是**与颜色无关**的通用信号，所以换成别的会场（比如红色边框、没有射灯）也能用：

🇬🇧 The crop and scan logic lives in `slide_crop.py` and relies on **color-agnostic** cues, so it transfers to other venues (e.g. red frames, or no spotlight bar):

- 🇨🇳 **上下边界**：幻灯片是亮的，射灯/天花板/观众是暗的 → 取最长的亮行区间。
  🇬🇧 **Top/bottom**: the slide is bright; spotlights/ceiling/audience are dark → take the longest run of bright rows.
- 🇨🇳 **左右边界**：装饰边框的颜色饱和度远高于内容 → 切到高饱和边带的内沿。
  🇬🇧 **Left/right**: the decorative frame is far more saturated than the content → cut to the inner edge of the saturated band.
- 🇨🇳 **扫描去色偏**：翻拍屏幕会让白底变浅蓝，用"白点白平衡"还原中性白，再拉平光照、锐化文字。
  🇬🇧 **Scan**: a tinted screen turns white into light blue; a white-patch white balance restores neutral white, then lighting is flattened and text sharpened.

🇨🇳 在 51 张人工标注的裁切上验证，平均边界误差 1.3%。
🇬🇧 Validated against 51 hand-made crops at 1.3% mean edge error.

---

## 📦 版本 / Changelog

- **2.1** — 🇨🇳 扫描件效果（白底质感，暗片自动跳过）；字体可配置（中文宋体 / 英文 Times New Roman），摘要字号可调。🇬🇧 Document-scan effect (clean white look, dark slides auto-skipped); configurable fonts and summary size.
- **2.0** — 🇨🇳 自动裁切（去边框/射灯/观众），颜色无关可泛化。🇬🇧 Automatic content cropping (frames/spotlights/audience removed), color-agnostic.
- **1.0** — 🇨🇳 视觉读图 + 制式生成 PPT。🇬🇧 Vision reading + consistent-layout PPTX generation.

---

## 📄 许可 / License

MIT

---

*🇨🇳 用 [Claude Code](https://claude.com/claude-code) / [腾讯 CodeBuddy](https://www.codebuddy.cn/) 构建 · 🇬🇧 Built with Claude Code / Tencent CodeBuddy*
