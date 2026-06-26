# -*- coding: utf-8 -*-
"""
会议总结 PDF 生成器模板（Canvas 绝对坐标渲染）
关键概念栏绘制在常量 BAR_Y 位置 — 物理上不可能溢出到下一页。

使用方法：
  1. 填写下方「配置区」的变量
  2. 填入 FOCUS_SLIDES 和 OTHER_SESSIONS 数据
  3. python generate_<会议简称>_pdf.py
"""

import os, re
from reportlab.pdfgen import canvas as _canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Frame, Spacer
from PIL import Image as PILImage

# ══════════════════════════════════════════════════════════════════════════════
# 配置区 — 每次新会议只需修改这里和下方的数据区
# ══════════════════════════════════════════════════════════════════════════════

FOCUS_DIR  = r'...\Library\...\Focus'   # Focus 照片目录
OTHER_DIR  = r'...\Library\...\Other'   # Other 照片目录（若无可设为 None）
OUTPUT_PDF = r'...\会议名_年份_报告.pdf'

CACHE_DIR  = r'C:\Temp\pdf_img_cache'   # 图片压缩缓存目录
os.makedirs(CACHE_DIR, exist_ok=True)

CONF_SUBTITLE   = 'CMAC · 生物医药新技术创新亦庄论坛'
CONF_DATE_VENUE = '2026年6月25日  ·  北京经济技术开发区亦庄'
CONF_EN_VENUE   = 'Beijing Economic and Technological Development Area'

FOCUS_LABEL    = 'FOCUS 重点报告'
FOCUS_SPEAKER  = '讲者姓名'
FOCUS_AFFIL    = '单位'
FOCUS_TITLE_ZH = '演讲题目（中文）'
FOCUS_TITLE_EN = 'Lecture Title (English)'
FOCUS_NOTE     = ''   # 自动填写

OTHER_TITLE_ZH  = '生物医药 · AI · 临床统计 · 大模型'
OTHER_TITLE_EN  = 'Pharmaceutical Innovation · AI · Clinical Statistics · LLM'
OTHER_SECTION_SPEAKER = '会议报告综述'
OTHER_SECTION_AFFIL   = '以下讲者关键信息摘要'

BAR_FOOTER = 'AI助力RWE  ·  讲者姓名  ·  CMAC  ·  2026-06-25'

# ══════════════════════════════════════════════════════════════════════════════
# 数据区 — 由视觉 AI 自动提取后填入
# ══════════════════════════════════════════════════════════════════════════════

FOCUS_SLIDES = [
    # (照片编号, '幻灯片标题', ['关键词1', '关键词2', '关键词3'],
    #  ['要点一，一到两句话', '要点二', '  → 子要点（两空格开头）']),
]

OTHER_SESSIONS = [
    # {
    #     'speaker': '讲者姓名',
    #     'affiliation': '单位职称',
    #     'title': '演讲题目中文',
    #     'en_title': 'Title in English',
    #     'slide_nums': [代表性照片编号1, 照片编号2, 照片编号3],
    #     'points': ['核心观点一', '  → 子观点', '', '核心观点二'],
    # },
]

# ══════════════════════════════════════════════════════════════════════════════
# 以下代码通常不需要修改
# ══════════════════════════════════════════════════════════════════════════════

DARK_BLUE  = HexColor('#0D3B6E')
MID_BLUE   = HexColor('#1565C0')
LIGHT_BLUE = HexColor('#8CB8E0')
ACCENT     = HexColor('#F4A261')
GREY_LINE  = HexColor('#CBD5E0')
TEXT_DARK  = HexColor('#1A202C')
TEXT_MUTED = HexColor('#4A5568')

BASE_FONT = 'Helvetica'
for _name, _path in [('MicrosoftYaHei', 'C:/Windows/Fonts/msyh.ttc'),
                      ('SimHei',         'C:/Windows/Fonts/simhei.ttf')]:
    if os.path.exists(_path):
        try:
            pdfmetrics.registerFont(TTFont(_name, _path))
            BASE_FONT = _name
            break
        except Exception:
            pass
print(f'Font: {BASE_FONT}')

def cm(x):
    return x * 28.3465

# ── Layout preset — change LAYOUT to switch ──────────────────────────────────
LAYOUT = '16:9'   # '16:9' (widescreen, default) | 'A4' (landscape, legacy)

if LAYOUT == '16:9':
    PAGE_W, PAGE_H   = cm(33.87), cm(19.05)   # 960 × 540 pt (standard widescreen)
    PHOTO_W, PHOTO_H = cm(19.50), cm(14.63)
    PHOTO_T_TOP      = cm(1.20)
    BAR_T_TOP        = cm(16.20)               # FIXED for this layout
    BAR_H            = cm(2.50)
else:                                           # A4 landscape
    PAGE_W, PAGE_H   = landscape(A4)           # 841.89 × 595.28 pt
    PHOTO_W, PHOTO_H = cm(20.80), cm(15.60)
    PHOTO_T_TOP      = cm(1.41)
    BAR_T_TOP        = cm(17.61)               # FIXED for this layout
    BAR_H            = cm(2.96)

PHOTO_X  = cm(1.20)
PHOTO_Y  = PAGE_H - PHOTO_T_TOP - PHOTO_H

BAR_X    = cm(1.20)
BAR_W    = PAGE_W - cm(2.40)
BAR_Y    = PAGE_H - BAR_T_TOP - BAR_H         # constant, cannot drift

RIGHT_X  = PHOTO_X + PHOTO_W + cm(0.15)
RIGHT_W  = PAGE_W - RIGHT_X - cm(1.20)


def get_path(folder, number):
    if not folder or not os.path.isdir(folder):
        return None
    import glob as _glob
    hits = _glob.glob(os.path.join(folder, f'*_{number}_*.jpg'))
    if hits:
        return hits[0]
    for f in os.listdir(folder):
        nums = re.findall(r'\d+', f)
        if len(nums) >= 2 and int(nums[-2]) == number:
            return os.path.join(folder, f)
        if nums and int(nums[-1]) == number:
            return os.path.join(folder, f)
    return None


def compress_photo(src, q=87):
    base = os.path.splitext(os.path.basename(src))[0]
    dst  = os.path.join(CACHE_DIR, f'{base}_300.jpg')
    if not os.path.exists(dst):
        with PILImage.open(src) as im:
            iw, ih = im.size
            target_w = int(20.80 / 2.54 * 300)
            target_h = int(15.60 / 2.54 * 300)
            scale = min(target_w / iw, target_h / ih, 1.0)
            nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
            out = im.resize((nw, nh), PILImage.LANCZOS) if scale < 1.0 else im
            out.convert('RGB').save(dst, 'JPEG', quality=q, optimize=True)
    return dst


def compress_other(src, q=82):
    base = os.path.splitext(os.path.basename(src))[0]
    dst  = os.path.join(CACHE_DIR, f'{base}_other.jpg')
    if not os.path.exists(dst):
        with PILImage.open(src) as im:
            iw, ih = im.size
            target_w = int(7.33 / 2.54 * 200)
            target_h = int(11.20 / 2.54 * 200)
            scale = min(target_w / iw, target_h / ih, 1.0)
            nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
            out = im.resize((nw, nh), PILImage.LANCZOS) if scale < 1.0 else im
            out.convert('RGB').save(dst, 'JPEG', quality=q, optimize=True)
    return dst


def S(name, **kw):
    return ParagraphStyle(name, fontName=BASE_FONT, **kw)

ST_TTL   = S('ttl',  fontSize=17, leading=23, textColor=DARK_BLUE)
ST_LBL   = S('lbl',  fontSize=10, leading=14, textColor=TEXT_MUTED)
ST_BLT   = S('blt',  fontSize=12, leading=18, textColor=TEXT_DARK,  spaceBefore=5, spaceAfter=2)
ST_SUB   = S('sub',  fontSize=10, leading=15, textColor=TEXT_MUTED, leftIndent=10, spaceBefore=1)
ST_BLBL  = S('blbl', fontSize=11, leading=15, textColor=LIGHT_BLUE)
ST_BTAG  = S('btag', fontSize=20, leading=26, textColor=white)
ST_BFOOT = S('bfoo', fontSize=10, leading=14, textColor=LIGHT_BLUE)
ST_CBIG  = S('cbig', fontSize=30, leading=38, textColor=white,               alignment=TA_CENTER)
ST_CSUB  = S('csub', fontSize=15, leading=21, textColor=HexColor('#BDD7F5'), alignment=TA_CENTER)
ST_CMETA = S('cmet', fontSize=12, leading=17, textColor=HexColor('#90B8D8'), alignment=TA_CENTER)
ST_DSEC  = S('dsec', fontSize=24, leading=31, textColor=white,               alignment=TA_CENTER)
ST_DNAM  = S('dnam', fontSize=20, leading=27, textColor=white,               alignment=TA_CENTER)
ST_DAFF  = S('daff', fontSize=12, leading=17, textColor=HexColor('#BDD7F5'), alignment=TA_CENTER)
ST_DTTL  = S('dttl', fontSize=14, leading=20, textColor=ACCENT,              alignment=TA_CENTER)
ST_DEN   = S('den',  fontSize=11, leading=16, textColor=HexColor('#BDD7F5'), alignment=TA_CENTER)
ST_SNAM  = S('snam', fontSize=22, leading=29, textColor=white,               alignment=TA_CENTER)
ST_BODY  = S('body', fontSize=12, leading=18, textColor=TEXT_DARK,  spaceBefore=5, spaceAfter=2)
ST_BIND  = S('bind', fontSize=10, leading=15, textColor=TEXT_MUTED, leftIndent=12, spaceBefore=1)


def draw_para(c, x, y_top, w, style, text, h_limit=9999):
    p = Paragraph(text, style)
    _, ah = p.wrapOn(c, w, h_limit)
    p.drawOn(c, x, y_top - ah)
    return ah


def fill_frame(c, x, y_top, w, h, story_items):
    f = Frame(x, y_top - h, w, h,
              leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, showBoundary=0)
    f.addFromList(list(story_items), c)


def dark_rect(c, x, y_bottom, w, h, color=None):
    c.setFillColor(color or DARK_BLUE)
    c.rect(x, y_bottom, w, h, fill=1, stroke=0)


def draw_cover(c):
    dark_rect(c, cm(1.20), cm(0.43), cm(27.30), PAGE_H - cm(0.86))
    stories = [
        Paragraph(CONF_SUBTITLE,   ST_CSUB),
        Spacer(1, 8),
        Paragraph('会 议 总 结',    ST_CBIG),
        Spacer(1, 10),
        Paragraph(CONF_DATE_VENUE, ST_CMETA),
        Paragraph(CONF_EN_VENUE,   ST_CMETA),
    ]
    fill_frame(c, cm(3), PAGE_H * 0.72, PAGE_W - cm(6), PAGE_H * 0.50, stories)


def draw_section_divider(c, label, name, affil, title_zh, title_en, note=''):
    dark_rect(c, cm(1.20), cm(0.43), cm(27.30), PAGE_H - cm(0.86))
    stories = [
        Paragraph(label,    ST_DSEC), Spacer(1, 14),
        Paragraph(name,     ST_DNAM), Spacer(1, 4),
        Paragraph(affil,    ST_DAFF), Spacer(1, 18),
        Paragraph(title_zh, ST_DTTL), Spacer(1, 4),
        Paragraph(title_en, ST_DEN),
    ]
    if note:
        stories += [Spacer(1, 8), Paragraph(note, ST_DEN)]
    fill_frame(c, cm(3), PAGE_H * 0.78, PAGE_W - cm(6), PAGE_H * 0.64, stories)


def draw_bar(c, tags):
    """Keyword bar — drawn at absolute constant BAR_Y, never drifts."""
    dark_rect(c, BAR_X, BAR_Y, BAR_W, BAR_H)
    pad_x   = BAR_X + cm(0.50)
    inner_w = BAR_W - cm(1.0)
    lbl_h = draw_para(c, pad_x, BAR_Y + BAR_H - cm(0.15), inner_w, ST_BLBL, '关键概念')
    draw_para(c, pad_x, BAR_Y + BAR_H - cm(0.15) - lbl_h - 2,
              inner_w, ST_BTAG, '  ·  '.join(tags))
    draw_para(c, pad_x, BAR_Y + cm(0.35), inner_w, ST_BFOOT, BAR_FOOTER)


def draw_focus_slide(c, idx, num, title, tags, bullets):
    photo_path = get_path(FOCUS_DIR, num)
    if photo_path:
        compressed = compress_photo(photo_path)
        c.drawImage(compressed, PHOTO_X, PHOTO_Y, width=PHOTO_W, height=PHOTO_H,
                    preserveAspectRatio=True, anchor='sw')
    else:
        dark_rect(c, PHOTO_X, PHOTO_Y, PHOTO_W, PHOTO_H, HexColor('#CCCCCC'))

    y = PAGE_H - cm(1.49)
    h = draw_para(c, RIGHT_X, y, RIGHT_W, ST_TTL, title)
    y -= h + 4
    h = draw_para(c, RIGHT_X, y, RIGHT_W, ST_LBL,
                  f'幻灯片 {idx+1} / {len(FOCUS_SLIDES)}  ·  照片 #{num}')
    y -= h + 6

    c.setStrokeColor(GREY_LINE)
    c.setLineWidth(0.6)
    c.line(RIGHT_X + cm(0.2), y, RIGHT_X + RIGHT_W - cm(0.2), y)
    y -= 8

    limit_y = BAR_Y + BAR_H + cm(0.12)
    for line in bullets:
        if y <= limit_y:
            break
        if line == '':
            y -= 5
        elif line.startswith('  ') or line.startswith('\t'):
            p = Paragraph(line.strip(), ST_SUB)
            _, ph = p.wrapOn(c, RIGHT_W, y - limit_y)
            if ph > 0 and y - ph >= limit_y:
                p.drawOn(c, RIGHT_X, y - ph)
                y -= ph + 2
        else:
            p = Paragraph(line, ST_BLT)
            _, ph = p.wrapOn(c, RIGHT_W, y - limit_y)
            if ph > 0 and y - ph >= limit_y:
                p.drawOn(c, RIGHT_X, y - ph)
                y -= ph + 5

    draw_bar(c, tags)


def draw_other_slide(c, sess):
    speaker    = sess['speaker']
    affil      = sess['affiliation']
    title_zh   = sess['title']
    title_en   = sess.get('en_title', '')
    photo_nums = sess.get('slide_nums', sess.get('photo_nums', []))
    points     = sess['points']

    HDR_H = cm(4.15)
    dark_rect(c, cm(1.20), PAGE_H - HDR_H, cm(27.30), HDR_H)

    hdr_items = [Paragraph(speaker, ST_SNAM), Spacer(1, 4), Paragraph(affil, ST_DAFF),
                 Spacer(1, 8), Paragraph(title_zh, ST_DTTL)]
    if title_en:
        hdr_items += [Spacer(1, 4), Paragraph(title_en, ST_DEN)]
    fill_frame(c, cm(1.70), PAGE_H - cm(0.15), cm(26.30), HDR_H - cm(0.30), hdr_items)

    TXT_TOP = PAGE_H - HDR_H - cm(0.25)
    body_items = []
    for line in points:
        if line == '':
            body_items.append(Spacer(1, 4))
        elif line.startswith('  ') or line.startswith('\t'):
            body_items.append(Paragraph(line.strip(), ST_BIND))
        else:
            body_items.append(Paragraph(line, ST_BODY))
    fill_frame(c, cm(1.30), TXT_TOP, cm(15.30), TXT_TOP - cm(0.50), body_items)

    PHO_X = cm(18.70)
    PHO_W = PAGE_W - PHO_X - cm(1.20)
    n     = min(len(photo_nums), 3)
    avail = PAGE_H - HDR_H - cm(0.50) - cm(0.50)
    if n > 0:
        ph_h = (avail - (n - 1) * cm(0.15)) / n
        for i, pnum in enumerate(photo_nums[:n]):
            ppath = get_path(OTHER_DIR, pnum) or get_path(FOCUS_DIR, pnum)
            if ppath:
                comp = compress_other(ppath)
                ph_y = PAGE_H - HDR_H - cm(0.25) - (i + 1) * ph_h - i * cm(0.15)
                c.drawImage(comp, PHO_X, ph_y, width=PHO_W, height=ph_h,
                            preserveAspectRatio=True, anchor='sw')


def build_pdf():
    global FOCUS_NOTE
    FOCUS_NOTE = FOCUS_NOTE or f'以下 {len(FOCUS_SLIDES)} 张幻灯片逐页解读'

    c = _canvas.Canvas(OUTPUT_PDF, pagesize=(PAGE_W, PAGE_H))

    print('封面...')
    draw_cover(c)
    c.showPage()

    if FOCUS_SLIDES:
        print('Focus 分节页...')
        draw_section_divider(c, FOCUS_LABEL, FOCUS_SPEAKER, FOCUS_AFFIL,
                             FOCUS_TITLE_ZH, FOCUS_TITLE_EN, FOCUS_NOTE)
        c.showPage()

        print(f'Focus 幻灯片 ({len(FOCUS_SLIDES)} 张)...')
        for idx, (num, title, tags, bullets) in enumerate(FOCUS_SLIDES):
            if (idx + 1) % 10 == 0:
                print(f'  ... {idx+1}/{len(FOCUS_SLIDES)}')
            draw_focus_slide(c, idx, num, title, tags, bullets)
            c.showPage()

    if OTHER_SESSIONS:
        print('Other 分节页...')
        draw_section_divider(c, 'OTHER 其他报告', OTHER_SECTION_SPEAKER, OTHER_SECTION_AFFIL,
                             OTHER_TITLE_ZH, OTHER_TITLE_EN)
        c.showPage()

        print('Other 讲者幻灯片...')
        for sess in OTHER_SESSIONS:
            print(f"  {sess['speaker']}")
            draw_other_slide(c, sess)
            c.showPage()

    c.save()
    print(f'\n完成 → {OUTPUT_PDF}')


if __name__ == '__main__':
    build_pdf()
