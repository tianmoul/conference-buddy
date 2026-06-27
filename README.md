# ConferenceBuddy · 会议幻灯片自动总结

[![latest release](https://img.shields.io/github/v/release/tianmoul/conference-buddy?label=version%20%E7%89%88%E6%9C%AC&sort=semver)](https://github.com/tianmoul/conference-buddy/releases/latest)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

> **In one line: turn a stack of messy, glare-covered phone photos of conference slides into a clean, uniformly-formatted summary deck — automatically.**
>
> **一句话：把一沓在台下随手拍的、带眩光色偏的会议幻灯片照片，自动变成一份排版统一、干净专业的总结 PPT。**

<p align="center"><img src="assets/pipeline.png" width="460" alt="pipeline"></p>

*Five steps (top → bottom): raw photo → auto-detect slide region → crop → scan to a clean document → finished slide.*
<br>*五步（从上到下）：原始照片 → 自动识别PPT区域 → 裁切 → 扫描成白底文档 → 成品幻灯片。*

> 🔒 **Privacy · 隐私** — In these README example images, all faces, the audience, and the slide content are pixelated, and the summary/keywords are shown as `XXXX`. This mosaic exists **only in the README images** — the actual tool produces clean, un-blurred output. · 示例图中人脸、观众和幻灯片内容均已打码，摘要/关键词用 `XXXX` 占位；打码**只存在于 README 示意图里**，真正的工具输出是清晰无码的。

---
---

# English

## ✨ The WOW Factor — from a messy photo to a finished slide

A photo you snap from the audience is rough: spotlights along the top, blue decorative frames on the sides, a blue color cast on the screen, rows of heads at the bottom, and glare. ConferenceBuddy **finds the real slide area → crops away the frames / spotlights / heads → restores the screen photo into a clean white "scanned document" → reads the content and writes Chinese bullet points → lays it into one consistent template** — with no manual cropping or data entry. See the five-step pipeline at the top.

## 🧠 What it does

You point it at a folder of conference slide photos, and it will:

1. **Scan** the folder, auto-detecting a `Focus/` + `Other/` layout, or treating everything as Focus.
2. **Auto-crop** each photo to the real slide region — frames, spotlights, audience removed.
3. **Scan** away the color cast / glare to a clean white "document" look (dark-themed slides are skipped automatically).
4. **Read** each slide with Claude vision — title, keywords, bullet points (in Chinese).
5. **Generate** a PPTX with a layout that never drifts page to page.

## 🚀 Installation & Deployment

ConferenceBuddy is a "Skill" — just a folder you drop into your AI coding assistant's skills directory. **Users in mainland China should use Tencent CodeBuddy (Option B)**, since Claude Code is not directly available there.

### 💡 Easiest of all — let the assistant install it for you

Don't want to touch a terminal? Just talk to **WorkBuddy** or **Claude Code** in plain language, and it will clone this repo into the skills directory:

```
Install the skill from https://github.com/tianmoul/conference-buddy
```

Then start a new chat and invoke it with `/conference-buddy`. The manual options below are only if you prefer to install it by hand.

### Prerequisites (for manual install)

```bash
pip install python-pptx Pillow opencv-python numpy
```

You also need the **SimSun (宋体)** and **Times New Roman** fonts (bundled with Windows) for Chinese rendering.

### Option A · Claude Code (international)

```bash
git clone https://github.com/tianmoul/conference-buddy.git
# Windows
xcopy /E /I conference-buddy "%USERPROFILE%\.claude\skills\conference-buddy"
# macOS / Linux
cp -r conference-buddy ~/.claude/skills/
```

Then in Claude Code say "conference summary" with the photo folder path.

### Option B · Tencent CodeBuddy (recommended in China)

CodeBuddy is Tencent Cloud's AI coding assistant; its CLI, **CodeBuddy Code**, works much like Claude Code and **supports Skills**.

**Step 1 — Install the CLI** (requires Node.js 18.20+):

```bash
npm install -g @tencent-ai/codebuddy-code
```

Or the Node-free native installer:

```powershell
# Windows (PowerShell)
irm https://www.codebuddy.cn/cli/install.ps1 | iex
```
```bash
# macOS / Linux
curl -fsSL https://www.codebuddy.cn/cli/install.sh | bash
```

**Step 2 — Drop the skill into `~/.codebuddy/skills/`** (`%USERPROFILE%\.codebuddy\skills\` on Windows):

```bash
git clone https://github.com/tianmoul/conference-buddy.git
# Windows
xcopy /E /I conference-buddy "%USERPROFILE%\.codebuddy\skills\conference-buddy"
# macOS / Linux
cp -r conference-buddy ~/.codebuddy/skills/
```

**Step 3 — Use it**: start `codebuddy` and invoke `/conference-buddy`.
Docs: https://www.codebuddy.ai/docs/zh/cli/installation

### Option C · WorkBuddy (Tencent's office-agent app)

**WorkBuddy** is Tencent's "office AI agent" desktop/mobile workspace for non-coders. Android users can search "**WorkBuddy**" in Huawei AppGallery, Xiaomi GetApps, or Tencent MyApp. ⚠️ WorkBuddy is the end-user product; installing and running Skills today is done through **CodeBuddy Code (Option B)**. Site: https://www.codebuddy.cn/work/

## 📂 Photo library layout

```
Library/
└── 2026_06_25_MyConf/
    ├── Focus/          ← main speaker, one slide per photo
    │   └── ...
    └── Other/          ← other speakers, 3 photos each
        └── ...
```

No subfolders is fine — every photo in the root is treated as a Focus slide.

## ⚙️ Configuration (optional)

All defaults work out of the box — you usually don't need this. The simplest way to change anything is to **ask the assistant in the conversation** (e.g. "make the summary font size 12"). Or edit the settings at the top of the generated script:

```python
FONT_ZH      = '宋体'                 # Chinese typeface
FONT_EN      = 'Times New Roman'      # Latin typeface
SUMMARY_SIZE = 14   # right-column summary size; bigger reads easier, smaller (11/12) fits more text
OTHER_SIZE   = 13   # other-speaker bullet size
SCAN_MODE    = 'auto'   # 'auto' (scan light, skip dark) | 'on' | 'off'
FORCE_NOSCAN = set()    # nums to always keep as a plain crop
LAYOUT       = '16:9'   # '16:9' widescreen (default) or 'A4' landscape
```

## 🗣️ How to trigger

Invoke it with the slash command, or just say a trigger phrase:

```
/conference-buddy
conference summary from Library/2026_06_25_MyConf
```

It asks for the conference name, date, and venue, analyzes each photo (~5–10 s each), then produces the PPTX and reports the file path and page count.

## 🛠️ How it works under the hood

The crop and scan logic lives in `slide_crop.py` and relies on **color-agnostic** cues, so it transfers to other venues (e.g. red frames, or no spotlight bar):

- **Top/bottom**: the slide is bright; spotlights/ceiling/audience are dark → take the longest run of bright rows.
- **Left/right**: the decorative frame is far more saturated than the content → cut to the inner edge of the saturated band.
- **Scan**: a tinted screen turns white into light blue; a white-patch white balance restores neutral white, then lighting is flattened and text sharpened.

Validated against 51 hand-made crops at 1.3% mean edge error.

## 📦 Changelog

- **2.1.1** — Configurable fonts (SimSun / Times New Roman) and adjustable summary size; bilingual README with a 5-step pipeline showcase.
- **2.1.0** — Document-scan effect (clean white look, dark slides auto-skipped).
- **2.0.0** — Automatic content cropping (frames/spotlights/audience removed), color-agnostic.
- **1.0.0** — Vision reading + consistent-layout PPTX generation.

## 📄 License

MIT — see [LICENSE](LICENSE).

---
---

# 中文

## ✨ 核心亮点（WOW）—— 从一张潦草照片到一页成品幻灯片

你在台下用手机拍的照片是这样的：上面一排射灯、左右蓝色装饰边框、屏幕偏蓝、下面全是观众后脑勺、还带着反光。ConferenceBuddy 会**自动识别中间真正的幻灯片区域 → 裁掉边框/射灯/人头 → 把翻拍屏幕还原成干净的白底"扫描件" → 读懂内容并写成中文要点 → 排进统一模板**，全程不需要手动抠图或录入。流程见页面顶部的五步图。

## 🧠 它做了什么

你把一个装满会议幻灯片照片的文件夹交给它，它会：

1. **扫描文件夹**，自动识别 `Focus/`（主讲）+ `Other/`（其他讲者）结构，或把所有照片当作主讲。
2. **自动裁切**：识别真正的 PPT 区域，去掉左右边框、上方射灯、下方观众。
3. **扫描还原**：去掉屏幕色偏/眩光，还原成干净白底"扫描件"（深色主题幻灯片自动跳过）。
4. **视觉读图**：用 Claude 视觉读懂每张幻灯片，提取标题、关键词、要点（中文）。
5. **制式生成**：排进一个版式永远一致的 PPT。

## 🚀 安装与部署

ConferenceBuddy 是一个"技能（Skill）"——本质就是一个文件夹，放进 AI 编程助手的技能目录即可。**中国大陆用户建议用腾讯 CodeBuddy（方案 B）**，因为 Claude Code 在国内无法直接使用。

### 💡 最省事：让助手自己装

懒得碰命令行？直接用大白话对 **WorkBuddy** 或 **Claude Code** 说，它就会把本仓库克隆到技能目录：

```
帮我安装这个仓库的 skill：https://github.com/tianmoul/conference-buddy
```

装好后新开一段对话，用 `/conference-buddy` 调用即可。下面的手动方案只是给想自己动手装的人备用。

### 前置依赖（手动安装时）

```bash
pip install python-pptx Pillow opencv-python numpy
```

还需要系统里有**宋体**和 **Times New Roman**（Windows 自带），用于中文渲染。

### 方案 A · Claude Code（国际用户）

```bash
git clone https://github.com/tianmoul/conference-buddy.git
# Windows
xcopy /E /I conference-buddy "%USERPROFILE%\.claude\skills\conference-buddy"
# macOS / Linux
cp -r conference-buddy ~/.claude/skills/
```

然后在 Claude Code 里说「会议总结 + 照片文件夹路径」即可。

### 方案 B · 腾讯 CodeBuddy（国内推荐）

CodeBuddy 是腾讯云的 AI 代码助手，其命令行版 **CodeBuddy Code** 用法与 Claude Code 基本一致，并且**支持 Skill**。

**第 1 步 — 安装 CLI**（需要 Node.js 18.20 以上）：

```bash
npm install -g @tencent-ai/codebuddy-code
```

或免 Node 的原生安装包：

```powershell
# Windows (PowerShell)
irm https://www.codebuddy.cn/cli/install.ps1 | iex
```
```bash
# macOS / Linux
curl -fsSL https://www.codebuddy.cn/cli/install.sh | bash
```

**第 2 步 — 把技能放进 `~/.codebuddy/skills/`**（Windows 为 `%USERPROFILE%\.codebuddy\skills\`）：

```bash
git clone https://github.com/tianmoul/conference-buddy.git
# Windows
xcopy /E /I conference-buddy "%USERPROFILE%\.codebuddy\skills\conference-buddy"
# macOS / Linux
cp -r conference-buddy ~/.codebuddy/skills/
```

**第 3 步 — 使用**：启动 `codebuddy`，用 `/conference-buddy` 调用。
官方文档：https://www.codebuddy.ai/docs/zh/cli/installation

### 方案 C · WorkBuddy（腾讯职场智能体 App）

**WorkBuddy** 是腾讯推出的"职场 AI 智能体"桌面/手机工作台，面向不写代码的普通办公用户。安卓用户可在华为应用市场、小米应用商店、应用宝搜索「**WorkBuddy**」下载。⚠️ WorkBuddy 偏向"终端用户"产品，技能的安装与运行目前以 **CodeBuddy Code（方案 B）** 为准。官网：https://www.codebuddy.cn/work/

## 📂 照片库结构

```
Library/
└── 2026_06_25_MyConf/
    ├── Focus/          ← 主讲，每张照片一页
    │   └── ...
    └── Other/          ← 其他讲者，每位 3 张
        └── ...
```

没有子文件夹也行——根目录里的所有照片都会被当作主讲幻灯片。

## ⚙️ 配置项（可选）

默认值开箱即用，一般用不到这里。最简单的改法是**直接在对话里跟助手说**（比如「把摘要字号调成 12」）。也可以手动改生成脚本顶部的参数：

```python
FONT_ZH      = '宋体'                 # 中文字体
FONT_EN      = 'Times New Roman'      # 英文字体
SUMMARY_SIZE = 14   # 右侧摘要字号；调大看得清楚，调小(11/12)能塞更多文字
OTHER_SIZE   = 13   # 其他讲者要点字号
SCAN_MODE    = 'auto'   # 自动(亮片扫描,暗片跳过) | 'on' 全扫 | 'off' 关闭
FORCE_NOSCAN = set()    # 强制不扫描的照片编号
LAYOUT       = '16:9'   # 宽屏(默认) 或 'A4' 横向
```

## 🗣️ 触发方式

用斜杠命令调用，或直接说关键词：

```
/conference-buddy
会议总结 D:\Library\2026_06_25_MyConf
```

它会先问你会议名称、日期、地点，逐张分析照片（每张约 5–10 秒），最后生成 PPT 并告诉你文件路径和页数。

## 🛠️ 技术原理

裁切和扫描的核心都在 `slide_crop.py`，用的是**与颜色无关**的通用信号，所以换成别的会场（比如红色边框、没有射灯）也能用：

- **上下边界**：幻灯片亮、射灯/天花板/观众暗 → 取最长亮行区间。
- **左右边界**：装饰边框饱和度远高于内容 → 切到高饱和边带内沿。
- **扫描去色偏**：翻拍屏幕让白底变浅蓝，用"白点白平衡"还原中性白，再拉平光照、锐化文字。

在 51 张人工标注裁切上验证，平均边界误差 1.3%。

## 📦 版本

- **2.1.1** — 字体可配置（中文宋体 / 英文 Times New Roman）、摘要字号可调；双语 README 加入 5 步流程展示图。
- **2.1.0** — 扫描件效果（白底质感，暗片自动跳过）。
- **2.0.0** — 自动裁切（去边框/射灯/观众），颜色无关可泛化。
- **1.0.0** — 视觉读图 + 制式生成 PPT。

## 📄 许可

MIT —— 见 [LICENSE](LICENSE)。

---

*Built with [Claude Code](https://claude.com/claude-code).*
