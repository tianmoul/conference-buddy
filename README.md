# ConferenceBuddy — Claude Code Skill

> **Auto-generate a professional conference summary PPTX from a folder of slide photos — no manual data entry.**
> 
> 从会议幻灯片照片库自动生成专业总结 PPTX，无需手动录入内容。

**Version 2.0**

---

## What's New in 2.0

- **Automatic slide-content cropping (`slide_crop.py`).** Conference photos show
  the slide on a decorated LED wall — colored side frames, stage spotlights, and
  audience heads around the real content. ConferenceBuddy now auto-crops every
  photo down to just the **presentation slide** ("PPT info region"), removing
  frames / spotlights / audience. The detector is **color-agnostic** (works with
  blue *or* red frames, with or without a spotlight bar) and was distilled from
  hand-made crops — validated at **1.3 % mean edge error over 51 photos**.
- **Tidier Other layout.** The 3 supporting-speaker thumbnails are cropped to a
  **uniform size** and laid out to fill the space neatly without overflowing the
  page.

---

## What It Does

You point ConferenceBuddy at a folder of conference slide photos. It:

1. **Scans** the folder — auto-detects `Focus/` + `Other/` structure, or treats everything as Focus slides
2. **Reads** each photo with Claude's vision — extracts speaker name, slide title, keywords, and key bullet points in Chinese
3. **Crops** each photo to the slide content — side frames, spotlights, and audience removed (`slide_crop.crop_content`)
4. **Generates** a ready-to-run Python script populated with all the extracted data
5. **Runs** the script — outputs a consistent-layout PPTX

Every slide gets one cropped photo, a keyword bar pinned at a fixed position, and a right-hand text column with the summary. The layout never drifts between pages.

---

## Example Output

| Element | Specification |
|---------|--------------|
| Format | PPTX (python-pptx) |
| Page size | **16:9 widescreen 33.87 × 19.05 cm** (default) · A4 landscape 29.70 × 21.00 cm (optional) |
| Photo area | 19.50 × 14.63 cm (16:9) · 20.80 × 15.60 cm (A4) |
| Keyword bar | Fixed at T = 16.20 cm (16:9) · 17.61 cm (A4) — never drifts |
| Photo quality | Original resolution, JPEG quality 87 |
| Typical output | ~40–50 slides, 80–150 MB PPTX |
| Switch layout | Set `LAYOUT = '16:9'` or `'A4'` in one line at the top of the script |

---

## Trigger Phrases

This skill activates automatically when you say anything like:

```
会议总结 Library/2026_09_15_APHA
会议报告 from today's photos
generate conference summary from my photo library
create conference PPTX from Library/2026_12_01_ASH
```

---

## Requirements

```bash
pip install python-pptx Pillow lxml
```

- **Claude Code** with vision (image reading) enabled
- **Windows / macOS / Linux** with Python 3.9+
- **Microsoft YaHei font** (`C:/Windows/Fonts/msyh.ttc`) for Chinese text — falls back to SimHei or Helvetica if not found

---

## Installation

### Option A — Claude Code skill (recommended)

```bash
# Copy to your Claude skills directory
cp -r conference-buddy ~/.claude/skills/
```

Then in Claude Code, just say `会议总结` or `generate conference summary` — the skill triggers automatically.

### Option B — Use the templates directly

Copy `templates/generate_pptx_template.py` or `templates/generate_report_template.py` to your project, fill in the config section at the top, and run:

```bash
python generate_MyConference.py
```

---

## Photo Library Structure

```
Library/
└── 2026_09_15_APHA/
    ├── Focus/          ← Main speaker slides (one PPTX slide per photo)
    │   ├── IMG_001_2.jpg
    │   ├── IMG_002_2.jpg
    │   └── ...
    └── Other/          ← Supporting speakers (grouped per speaker, 3 photos each)
        ├── IMG_042_2.jpg
        └── ...
```

**No subfolders?** ConferenceBuddy treats every photo in the root as a Focus slide.

---

## Workflow

```
User: "会议总结 Library/2026_09_15_APHA"
  │
  ├── Claude asks: conference name, date, venue
  ├── Scans folder → builds photo index (sorted by filename number)
  ├── For each photo → Read tool → vision extraction:
  │     title (Chinese, ≤20 chars)
  │     tags  (3–5 key concepts, English proper nouns kept)
  │     bullets (3–5 points in Chinese)
  │     speaker name + affiliation (from first/title slide)
  │
  ├── Writes generate_APHA2026.py (populated from template)
  ├── Runs it → APHA_2026_会议总结.pptx
  └── Reports: "Done — 47 slides, output at d:\..."
```

---

## Layout (Fixed — Do Not Modify)

```
┌──────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────┐  ┌────────────────────────┐ │
│  │                                 │  │  Slide Title           │ │
│  │                                 │  │  幻灯片 3 / 39         │ │
│  │         Photo (20.80cm)         │  │  ─────────────────     │ │
│  │         15.60cm tall            │  │  • Key point 1         │ │
│  │         Original resolution     │  │  • Key point 2         │ │
│  │                                 │  │    → sub-point         │ │
│  └─────────────────────────────────┘  └────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ 关键概念  RWE · AI辅助 · 因果推断    ConferenceName · Date  │ │  ← always at T=17.61cm
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Customization

All per-conference settings live in the **config section** at the top of the generated script. You never need to touch the rendering code below it.

```python
CONF_SUBTITLE   = 'APHA Annual Meeting 2026'
CONF_DATE_VENUE = '2026年9月15日  ·  Washington D.C.'
FOCUS_SPEAKER   = 'Jane Smith'
FOCUS_AFFIL     = 'Harvard School of Public Health'
BAR_FOOTER      = 'APHA  ·  Jane Smith  ·  2026-09-15'
```

---

## Language Behavior

| Content | Language |
|---------|----------|
| Slide titles | Chinese (translated if original is English) |
| Bullet points | Chinese |
| Technical terms | Original form kept (RWE, AI, LLM, SGLT-2, TTE…) |
| Speaker names | Original form kept (romanized or Chinese) |
| Conference metadata | Matches what user provides |

---

## License

MIT — free to use and adapt for any conference.

---

*Built with [Claude Code](https://claude.ai/code) · Skill format compatible with [SkillsMP](https://skillsmp.com/)*
