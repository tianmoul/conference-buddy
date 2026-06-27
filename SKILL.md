---
name: conference-buddy
version: 2.1.0
description: |
  Automatically generate a professional conference summary PPTX from a folder of slide photos. Uses vision AI to read each photo and extract speaker names, slide titles, keywords, and bullet points — no manual data entry needed.

  Trigger this skill whenever the user mentions any of the following:
  - "conference report", "conference summary", "generate slides from photos", "conference PPTX"
  - "会议报告"、"会议总结"、"会议幻灯片"、"生成报告"、"从照片生成总结"
  - User provides a folder path containing conference slide photos and wants a summary document

  Output: consistent-layout PPTX — one photo per slide, keyword bar pinned at a fixed position on every page, large clear images. Supports Focus/Other folder structure or flat folder (all treated as Focus slides).
compatibility:
  python_packages:
    - python-pptx
    - Pillow
---

# ConferenceBuddy — 会议报告生成器

## Overview / 功能概览

ConferenceBuddy turns a folder of conference slide photos into a polished summary PPTX. Given a photo library, it:

1. **Scans** the folder structure (auto-detects `Focus/` + `Other/` or treats all photos as Focus)
2. **Reads** each photo with vision AI and extracts title, keywords, and key points in Chinese
3. **Generates** a conference-specific Python script from the bundled template
4. **Runs** the script to produce a PPTX with pixel-perfect consistent layout

---

## Step 1 — Collect Info / 信息收集

Ask the user for (if not already provided):

| Field | Required | Example |
|-------|----------|---------|
| Photo library path 照片库路径 | ✓ | `d:\Conferences\Library\2026_09_15_APHA` |
| Conference name 会议名称 | ✓ | `APHA Annual Meeting` |
| Date 日期 | ✓ | `2026年9月15日` |
| Venue 地点 | ✓ | `Washington D.C.` |
| Output format 输出格式 | — | PPTX only |

---

## Step 2 — Scan Folder & Build Photo Index / 扫描文件夹

```python
import os, glob, re

library_path = r'...'

focus_dir = os.path.join(library_path, 'Focus')
other_dir = os.path.join(library_path, 'Other')

has_focus = os.path.exists(focus_dir)
has_other = os.path.exists(other_dir)

# No subfolders → treat everything as Focus
if not has_focus and not has_other:
    focus_dir = library_path
    has_focus = True
    has_other = False
```

**Sorting rule / 排序规则**: Extract the trailing number from each filename and sort numerically:

```python
def photo_key(path):
    nums = re.findall(r'\d+', os.path.basename(path))
    return int(nums[-1]) if nums else 0

focus_photos = sorted(glob.glob(os.path.join(focus_dir, '*.jpg')) +
                      glob.glob(os.path.join(focus_dir, '*.jpeg')),
                      key=photo_key)
```

Assign each photo an integer `num` (from filename or sequential index). This `num` is used as the first field in `FOCUS_SLIDES`.

---

## Step 3 — Vision Analysis / 视觉分析每张照片

This is the core step. Use the `Read` tool on each `.jpg`/`.jpeg` file to view the slide, then extract content.

### Focus Photos (one slide per page)

Extract for each Focus photo:

| Field | Requirement | Notes |
|-------|-------------|-------|
| `title` | ≤20 chars, **Chinese** | Slide title; translate English titles to Chinese |
| `tags` | 3–5 terms | Key concepts/methods; keep English proper nouns (RWE, AI, TTE) |
| `bullets` | 3–5 lines, **Chinese** | Key points in your own words; sub-points use two-space indent |

(The document-scan in Step 3.6 is automatic — no per-slide field to extract.)

**Language rule / 语言规则**: Output in Chinese by default. Keep technical proper nouns in original form (RWE, AI, LLM, SGLT-2, TTE, etc.).

**Format example / 格式示例:**
```python
(42, 'AI助力真实世界研究',
 ['RWE', 'AI辅助', '因果推断'],
 ['真实世界数据缺乏随机性，混杂因素控制是核心挑战',
  'AI可辅助识别混杂因素并建立倾向性评分',
  '  → 方法：IPTW / MSM 是当前主流控制手段'])
```

### Identify Focus Speaker / 识别 Focus 讲者

Usually the first slide (title page) contains speaker name, affiliation, and talk title. Extract:
- `speaker_name` — e.g. `詹思延`
- `speaker_affil` — e.g. `北京大学公共卫生学院院长`
- `focus_title_zh` — talk title in Chinese
- `focus_title_en` — talk title in English (if present)

### Other Photos (grouped by speaker) / Other 照片

Other photos are typically ordered by speaker, with multiple consecutive slides per speaker. Identify speaker boundaries by looking for title/intro slides with name and affiliation.

For each Other speaker:

```python
{
    'speaker': 'Speaker Name',
    'affiliation': 'Institution / Title',
    'title': '演讲题目中文',
    'en_title': 'Talk Title in English',
    'photo_nums': [68, 74, 80],  # 2–3 representative slide numbers
    'points': [
        '核心观点一（1-2句话）',
        '  → 子观点（两空格缩进）',
        '',                         # '' = blank line / paragraph break
        '核心观点二',
    ],
}
```

**Choose representative photos**: prefer slides with charts or key data, not pure text pages.

---

## Step 3.5 — Crop Photos to the Slide Content / 照片裁切（slide_crop.py）

Conference photos show the speaker's slide on a decorated LED wall: the slide is
flanked LEFT/RIGHT by colored decorative frames, capped ABOVE by stage
spotlights, and bordered BELOW by audience heads. The report should show **only
the slide itself** (the "PPT info region") — frames, spotlights, and audience
removed. The bundled **`slide_crop.py`** does this automatically.

```python
import slide_crop                       # bundled next to this skill

# One clean crop (returns a PIL.Image): frames + spotlights + audience removed
img = slide_crop.crop_content(photo_path)

# Force a UNIFORM pixel size (aspect may break) — use for the Other 3-up stack
# so the stacked thumbnails line up perfectly:
img = slide_crop.crop_content(photo_path, target_size=(1600, 900))

# Just the box, if you need coordinates: (left, top, right, bottom)
box = slide_crop.detect_content_region(cv2_bgr_image)
```

**How it generalizes (no hard-coded colors).** It was distilled from a user's
manual crops and validated at 1.3 % mean edge error over 51 photos. Two
color-agnostic cues, so it transfers to other venues (e.g. **red** frames, or
**no** spotlight bar):

- **Top / Bottom** — the slide is BRIGHT; spotlights/ceiling and audience are
  DARK. Take the longest run of bright rows. (Colored spotlights are bright
  *dots* but a dark *row average*, so brightness, not saturation, is used here.)
  For a dark slide where brightness can't cut an edge, it falls back to
  SATURATION for that edge (a deep-blue slide is saturated; ceiling/audience are
  not).
- **Left / Right** — the decorative frame is a band whose color SATURATION is
  far higher than the slide content (a solid panel vs. text/charts). Cut to the
  inner edge of the high-saturation edge band. A uniformly-saturated slide has
  no distinct frame and is kept full width.

**Usage in the generated script:**
- **Focus** photos → `crop_content(path)`, placed preserving aspect ratio so the
  ~16:9 slide fills the photo area without distortion.
- **Other** photos → `crop_content(path, target_size=(1600, 900))` so all three
  thumbnails are identical size and stack neatly (uniform size is preferred over
  preserving aspect for the Other column).

If a future venue behaves differently, the tunables at the top of
`detect_content_region` (`_C_BRIGHT_THR`, `_C_FRAME_REL`, `_C_FRAME_CAP`,
`_C_UNIFORM`, …) are the knobs to adjust.

---

## Step 3.6 — Document-Scan Effect / 扫描件效果

ConferenceBuddy renders each cropped slide as a clean **scanned document** — flat
white background, crisp dark text — via `crop_content(path, scan='auto')`. It
**white-balances** the slide (these are photos of a *color-tinted* screen, so a
truly white slide photographs as e.g. light blue — white balance restores it),
then flattens the lighting/glare and sharpens the text, giving that "original-PPT
/ scan" quality. Colored figures and highlights are preserved.

**It is automatic and safe.** `scan='auto'` (the default) scans every slide
**except dark-themed ones**, which it auto-detects by brightness and leaves as a
plain crop — scanning a dark slide would wash it out. So most light/white slides
(the vast majority of academic decks) become clean documents, and the few
dark-background title/section slides keep their original look.

Control it via the config near the top of the generated script:

```python
SCAN_MODE    = 'auto'     # 'auto' (scan light, skip dark) | 'on' (all) | 'off'
FORCE_NOSCAN = set()      # nums to always keep as a plain crop, e.g. {26, 27}
```

The template's `cropped_photo()` applies this to Focus and Other alike. No
per-slide vision flag is needed — the dark-slide skip is handled by the
brightness heuristic (`_C_DARK_MED` in slide_crop.py).

**Workflow order**: crop first, then scan — `crop_content` crops to the slide
content and applies `document_scan` to the result, so frames/spotlights/audience
are gone before the scan runs.

---

## Step 4 — Generate Conference Script / 生成会议专属脚本

Read the bundled template:
- `templates/generate_pptx_template.py` → PPTX output

Copy **`slide_crop.py`** next to the generated script so `import slide_crop`
works, then crop every photo through `crop_content` as described in Step 3.5.
Populate `SCAN_NUMS` from the `scan` flags collected in Step 3 (see Step 3.6).

Steps / 步骤:
1. Copy the template to the output directory (same level as the photo library)
2. Fill in the config section at the top (paths, conference name, speaker info)
3. Insert the `FOCUS_SLIDES` and `OTHER_SESSIONS` data extracted from photos
4. Save as `generate_{ConferenceAbbr}.py`

**Config variables to update / 需要修改的配置变量:**

```python
FOCUS_DIR = r'...\Library\...\Focus'
OTHER_DIR = r'...\Library\...\Other'
OUTPUT    = r'...\ConferenceName_Year_Summary.pptx'

CONF_SUBTITLE   = 'Conference Full Name'
CONF_DATE_VENUE = '2026年X月X日  ·  Venue'
CONF_EN_VENUE   = 'City, Country'

FOCUS_SPEAKER  = 'Speaker Name'
FOCUS_AFFIL    = 'Institution'
FOCUS_TITLE_ZH = '演讲题目中文'
FOCUS_TITLE_EN = 'Talk Title in English'

BAR_FOOTER = 'ConferenceAbbr  ·  Speaker  ·  YYYY-MM-DD'
```

**Output naming / 输出命名建议:**
- PPTX: `{ConferenceAbbr}_{Year}_会议总结.pptx`

---

## Step 5 — Run & Output / 执行输出

```python
import subprocess, sys
result = subprocess.run([sys.executable, script_path],
                       capture_output=True, text=True, encoding='utf-8')
print(result.stdout)
if result.returncode != 0:
    print('ERROR:', result.stderr)
```

Report the output file path and total page count to the user.

---

## Layout Constants / 布局参数

Set `LAYOUT = '16:9'` or `LAYOUT = 'A4'` at the top of the generated script. The rest of the code adapts automatically.

### 16:9 Widescreen — default / 默认（标准宽屏 33.87 × 19.05 cm）

| Element | L | T | W | H |
|---------|---|---|---|---|
| Photo 照片 | 1.20 | 1.20 | 19.50 | 14.63 |
| Keyword bar 关键概念栏 | 1.20 | **16.20 (fixed!)** | 31.47 | 2.50 |
| Right text column 右列 | 20.85 | 1.20 | ~11.82 | — |

### A4 Landscape — legacy / 备用（A4 横向 29.70 × 21.00 cm）

| Element | L | T | W | H |
|---------|---|---|---|---|
| Photo 照片 | 1.20 | 1.41 | 20.80 | 15.60 |
| Keyword bar 关键概念栏 | 1.20 | **17.61 (fixed!)** | 27.30 | 2.96 |
| Right text column 右列 | 22.15 | 1.49 | ~6.35 | — |

---

## Photo Lookup / 照片查找函数

Templates default to matching filenames by trailing number (`*_{num}_*.jpg`). If the new conference uses a different naming scheme, update `find_photo` / `get_path`:

```python
def find_photo(num, folder):
    for f in os.listdir(folder):
        nums = re.findall(r'\d+', f)
        if nums and int(nums[-1]) == num:
            return os.path.join(folder, f)
    return None
```

---

## Notes / 注意事项

- **Vision analysis takes time / 分析需要时间**: ~5–10s per photo; keep the user informed of progress.
- **Blurry photos / 照片模糊**: Mark as `(照片模糊，内容待确认)` with empty placeholder bullets; remind user to fill in after generation.
- **Charts and data slides / 图表页**: Extract the numbers and conclusions shown, not a description of the chart shape.
- **Chinese output by default / 中文优先**: Even if the original slides are in English, write bullets in Chinese. Keep English proper nouns as-is.
