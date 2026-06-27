# -*- coding: utf-8 -*-
"""
slide_crop.py — conference slide screen detector & cropper (v2)

Works on LED-wall conference photos where:
  - the slide screen is a large, uniformly bright rectangular area
  - stage spotlights appear at the top (isolated bright dots, not uniform)
  - audience is a dark band at the bottom

Main strategy: row/column brightness projection.
  Each LED-screen row has HIGH average brightness (the whole row is lit).
  A spotlight row has LOW average brightness (most of the row is dark ceiling).
  → threshold on row average reliably separates screen from ceiling/audience.
"""

import io
import cv2
import numpy as np
from PIL import Image


# ── Helpers ───────────────────────────────────────────────────────────────────

def _imread(path):
    """cv2.imread that handles Unicode/CJK filenames on Windows."""
    buf = np.fromfile(path, dtype=np.uint8)
    if buf.size == 0:
        return None
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)


# ══════════════════════════════════════════════════════════════════════════════
# CONTENT-REGION DETECTOR  (v6 — distilled from the user's manual crops)
#
# Goal: from a photo of a slide shown on a decorated LED wall, return ONLY the
# presentation slide ("PPT info region") — dropping the colored side frames, the
# spotlight bar above, and the audience heads below.
#
# It is built on two GENERAL, color-agnostic cues so it transfers to other
# venues (e.g. red frames instead of blue, no spotlight bar, etc.):
#
#   TOP / BOTTOM edge — the slide is BRIGHT; the ceiling/spotlights and the
#       audience are DARK. Take the longest run of bright rows. Colored
#       spotlights are bright *dots* but a dark *row average*, so brightness
#       (not saturation) is the right cue here. For dark slides (e.g. a deep-
#       blue title page) brightness can fail to cut, so when an edge is not
#       trimmed we fall back to SATURATION for that edge only — a dark-blue
#       slide is highly saturated while ceiling/audience are not.
#
#   LEFT / RIGHT edge — the decorative frame is a narrow band at the edge whose
#       colour SATURATION is far higher than the slide content (a solid blue/red
#       panel vs. text-and-charts content). Find the high-saturation band near
#       each edge and cut to its INNER edge. A uniformly-saturated slide (high
#       saturation across most of its width) has no distinct frame and is kept
#       full width. Saturation — not hue — drives this, so it transfers to red
#       frames or any other colour.
#
# Validated against 51 hand-made crops (39 Focus + 12 Other): mean per-edge
# error 1.3 %, max 4.7 %, zero photos above 5 %.
# ══════════════════════════════════════════════════════════════════════════════

# Tunables (fractions of image size unless noted)
_C_BLUR        = 21      # gaussian blur kernel for profiles
_C_BRIGHT_THR  = 0.60    # row is "slide" if brightness > this × centre median
_C_SAT_THR     = 0.62    # fallback: row is "slide" if saturation > this × median
_C_FRAME_REL   = 0.80    # frame columns have saturation > this × max column sat
_C_FRAME_FLOOR = 150.0   # ...but never below this absolute saturation
_C_FRAME_CAP   = 0.26    # search this fraction inward from each edge for a frame
_C_UNIFORM     = 0.60    # if > this fraction of columns are high-sat → no frame


def _close1d(mask, k):
    if k < 3:
        return mask > 0
    m = mask.astype(np.uint8).reshape(-1, 1)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((k, 1), np.uint8))
    return m.flatten() > 0


def _frame_edge(high, w, side):
    """Inner edge of a saturated decorative side frame, or the image edge."""
    if high.mean() > _C_UNIFORM:               # uniform-saturation slide: no frame
        return 0 if side == 'L' else w
    cap = int(w * _C_FRAME_CAP)
    if side == 'L':
        idx = np.where(high[:cap])[0]
        if len(idx) == 0:
            return 0
        j = int(idx[-1])
        while j < w and high[j]:                # extend through the frame band
            j += 1
        return j if j <= int(w * 0.30) else 0
    else:
        idx = np.where(high[w - cap:])[0]
        if len(idx) == 0:
            return w
        j = (w - cap) + int(idx[0])
        while j > 0 and high[j - 1]:
            j -= 1
        return j if j >= int(w * 0.70) else w


def detect_content_region(img_bgr):
    """
    Return (left, top, right, bottom) of the slide content, or None.

    See the module section above for the algorithm rationale.
    """
    h, w = img_bgr.shape[:2]
    blur = cv2.GaussianBlur(img_bgr, (_C_BLUR, _C_BLUR), 0)
    gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY).astype(np.float32)
    sat  = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)[:, :, 1].astype(np.float32)

    L, R = int(w * 0.25), int(w * 0.75)
    T, B = int(h * 0.10), int(h * 0.90)

    for _ in range(4):
        # ── TOP / BOTTOM via brightness, per-edge saturation fallback ─────────
        rv  = gray[:, L:R].mean(axis=1)
        rfv = np.median(rv[int(h * 0.4): int(h * 0.6)])
        if rfv < 5:
            return None
        rmask = _close1d(rv > rfv * _C_BRIGHT_THR, max(5, h // 25))
        T, B = _longest_run(rmask)

        if T < 0.08 * h or B > 0.92 * h or (B - T) > 0.85 * h:
            rs  = sat[:, L:R].mean(axis=1)
            rfs = np.median(rs[int(h * 0.4): int(h * 0.6)])
            T2, B2 = _longest_run(_close1d(rs > rfs * _C_SAT_THR, max(5, h // 25)))
            if 0.15 * h < (B2 - T2) < 0.85 * h:
                if (B - T) > 0.85 * h:
                    T, B = T2, B2
                else:
                    if T < 0.08 * h and 0.10 * h < T2 < 0.45 * h:
                        T = T2
                    if B > 0.92 * h and 0.55 * h < B2 < 0.92 * h:
                        B = B2
        if B <= T:
            T, B = int(h * 0.10), int(h * 0.90)

        # ── LEFT / RIGHT via saturated edge-frame ────────────────────────────
        cs   = sat[T:B, :].mean(axis=0)
        thr  = max(_C_FRAME_FLOOR, _C_FRAME_REL * cs.max())
        high = _close1d(cs > thr, max(3, w // 80))
        L = _frame_edge(high, w, 'L')
        R = _frame_edge(high, w, 'R')
        if R <= L:
            L, R = 0, w

    return L, T, R, B


def _longest_run(mask):
    """
    Return (start, end) indices of the longest contiguous True run in 1D mask.
    Ties broken by choosing the run with higher average value.
    """
    best_start, best_end, best_len = 0, len(mask), 0
    in_run = False
    cur_start = 0
    for i, v in enumerate(mask):
        if v and not in_run:
            in_run, cur_start = True, i
        elif not v and in_run:
            in_run = False
            length = i - cur_start
            if length > best_len:
                best_len, best_start, best_end = length, cur_start, i
    if in_run:
        length = len(mask) - cur_start
        if length > best_len:
            best_start, best_end = cur_start, len(mask)
    return best_start, best_end


# ── Primary: row/column projection ───────────────────────────────────────────

def _smooth1d(a, k):
    k = max(11, k)
    if k % 2 == 0:
        k += 1
    return np.convolve(a, np.ones(k) / k, mode='same')


# Calibrated for the CMAC LED stage. The screen is a fixed physical object, so
# every photo's crop should land on roughly the same width-to-height ratio.
# Close-up shots whose detected ratio falls below AR_MIN have caught audience
# rows at the bottom — we re-derive the bottom edge from AR_TARGET to cut them.
AR_MIN    = 2.05
AR_TARGET = 2.22


def _detect_by_projection(img_bgr):
    """
    Conference LED-screen pattern detector (v4 "blue-frame + brightness band").

    The CMAC stage has a fixed visual pattern: the speaker's slide is flanked
    LEFT and RIGHT by blue decorative panels, capped ABOVE by a bar of colored
    spotlights, and bordered BELOW by rows of audience heads. The rectangle
    those four features enclose is the real, information-bearing screen.

    Detection follows that pattern directly:

    LEFT / RIGHT
        The blue side panels are the most reliable anchor. We project the CMAC
        blue mask onto the column axis and find the dominant blue peak in each
        half independently (robust when one panel is partly occluded by slide
        content). Each panel's outer edge becomes the crop boundary; a weak
        peak means the panel runs off-frame, so we extend to the image edge.

    TOP / BOTTOM
        Within the blue-framed width, the screen is the longest run of bright
        rows — the dark ceiling above and the dark audience below break the run
        naturally. A valley-correction nudges the top below the spotlight bar
        when the screen starts at the very top of the frame.

    ASPECT RATIO
        Because the screen is one physical object, all crops should share a
        ratio. Crops that come out too tall (audience caught at the bottom) are
        tightened to AR_TARGET, keeping every output proportionally consistent.

    Returns (x, y, w, h) bounding box, or None if the image is too dark.
    """
    h, w = img_bgr.shape[:2]

    # ── LEFT / RIGHT: independent blue-panel peaks ────────────────────────────
    hsv  = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    bmask = (cv2.inRange(hsv, np.array([100, 80, 25]),
                              np.array([145, 255, 210])) // 255).astype(np.float32)
    col_blue = _smooth1d(bmask.mean(axis=0), w // 120)

    lhalf = int(w * 0.45)
    rhalf = int(w * 0.55)
    lc = int(np.argmax(col_blue[:lhalf]))
    rc = rhalf + int(np.argmax(col_blue[rhalf:]))
    lpk, rpk = col_blue[lc], col_blue[rc]

    PANEL_MIN = 0.28          # below this the panel is off-frame / not present
    EDGE_FRAC = 0.35          # outer edge = where blue falls to this × peak
    if lpk < PANEL_MIN:
        left = 0
    else:
        left = lc
        while left > 0 and col_blue[left] > lpk * EDGE_FRAC:
            left -= 1
    if rpk < PANEL_MIN:
        right = w
    else:
        right = rc
        while right < w - 1 and col_blue[right] > rpk * EDGE_FRAC:
            right += 1

    # Both side panels weak → this is a wide-angle / rear-of-hall shot where the
    # screen is small and not flanked by detectable blue. Defer to the blue blob
    # detector, which is designed for that case.
    if lpk < PANEL_MIN and rpk < PANEL_MIN:
        return None

    # ── TOP / BOTTOM: longest bright-row run within the framed width ──────────
    blurred = cv2.GaussianBlur(img_bgr, (31, 31), 0)
    gray    = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY).astype(np.float32)
    row_s   = _smooth1d(gray[:, left:right].mean(axis=1), h // 60)

    ref = np.median(row_s[int(h * 0.4): int(h * 0.6)])
    if ref < 10:
        return None
    bright = (row_s > ref * 0.55).astype(np.uint8).reshape(-1, 1)
    bright = cv2.morphologyEx(bright, cv2.MORPH_CLOSE,
                              np.ones((max(15, h // 40), 1), np.uint8)).flatten() > 0
    top, bottom = _longest_run(bright)
    if bottom <= top:
        top, bottom = int(h * 0.12), int(h * 0.80)

    # Blue-frame top edge — the decisive cut for the spotlight bar. The blue
    # side panels begin exactly at the screen's physical top; the spotlights and
    # ceiling above them carry no blue. So the upper edge of the blue frame is
    # the most reliable top boundary, and it works even on DARK slides where the
    # spotlight bar is brighter than the screen content and brightness alone
    # cannot separate lamps from screen. The slide title lives inside the blue
    # frame, so this never clips title text. Trust only the side(s) with a
    # strong panel and take the lower (more conservative) of the two edges.
    strip = max(3, int(w * 0.02))
    blue_tops = []
    if lpk >= PANEL_MIN:
        lt, _ = _longest_run(
            _smooth1d(bmask[:, max(0, lc - strip):lc + strip].mean(axis=1),
                      h // 80) > 0.35)
        blue_tops.append(lt)
    if rpk >= PANEL_MIN:
        rt, _ = _longest_run(
            _smooth1d(bmask[:, max(0, rc - strip):rc + strip].mean(axis=1),
                      h // 80) > 0.35)
        blue_tops.append(rt)
    blue_tops = [t for t in blue_tops if t > 0]
    if blue_tops:
        top = max(top, min(blue_tops))

    # ── Aspect-ratio consistency: tighten over-tall crops (audience caught) ──
    width = right - left
    if width > 0 and (bottom - top) > 0 and width / (bottom - top) < AR_MIN:
        bottom = top + int(width / AR_TARGET)

    if (right - left) < int(w * 0.20) or (bottom - top) < int(h * 0.18):
        return None

    return left, top, right - left, bottom - top


def _has_blue_sides(img_bgr, y_top, y_bottom, min_frac=0.12):
    """
    Return True if both the left-10 % and right-10 % strips of the detected
    row band contain enough CMAC dark-blue pixels.

    The CMAC LED screen always has blue decorative side panels (left panel:
    BICE/AI logo, right panel: conference branding). If the projection result
    does not have blue on both sides it is likely a wide-angle shot where the
    crop caught audience rows rather than the screen.
    """
    h, w = img_bgr.shape[:2]
    strip = max(1, int(w * 0.10))
    # Use only the middle 70 % of the vertical band to avoid ceiling/audience
    # rows that dilute the blue-panel fraction.
    band = y_bottom - y_top
    margin = int(band * 0.15)
    yt = y_top + margin
    yb = y_bottom - margin
    if yb <= yt:
        yt, yb = y_top, y_bottom
    roi_l = img_bgr[yt:yb, :strip]
    roi_r = img_bgr[yt:yb, w - strip:]
    lo = np.array([100,  80, 20])
    hi = np.array([145, 255, 210])
    for roi in (roi_l, roi_r):
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        frac = float(np.mean(cv2.inRange(hsv, lo, hi) > 0))
        if frac < min_frac:
            return False
    return True


# ── Second-pass: CMAC blue-screen color detector ─────────────────────────────

def _detect_by_blue(img_bgr):
    """
    Detect the CMAC LED screen by its distinctive dark-blue background color.

    Works for wide-angle / rear-of-hall shots where the screen is small and the
    projection method's AR check rejects the (too-tall) result.

    CMAC background: dark saturated blue
      OpenCV HSV → H ≈ 100–145, S > 80, V = 25–200
    """
    h, w = img_bgr.shape[:2]
    hsv  = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    lo = np.array([100,  80,  25])
    hi = np.array([145, 255, 200])
    mask = cv2.inRange(hsv, lo, hi)

    ker  = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, ker, iterations=5)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  ker, iterations=2)

    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    # Prefer landscape contours — side panels are portrait (AR < 0.8) and
    # should not be mistaken for the slide screen.
    landscape = [c for c in cnts
                 if cv2.boundingRect(c)[2] / max(cv2.boundingRect(c)[3], 1) >= 0.8]
    largest = max(landscape if landscape else cnts, key=cv2.contourArea)
    if cv2.contourArea(largest) < 0.04 * h * w:
        return None
    return cv2.boundingRect(largest)


# ── Third-pass: generic brightness + saturation blob ─────────────────────────

def _detect_by_hsv(img_bgr):
    """Backup: find brightest large saturated blob and return its bounding box."""
    h, w = img_bgr.shape[:2]
    hsv  = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    s_m  = cv2.threshold(hsv[:, :, 1],  40, 255, cv2.THRESH_BINARY)[1]
    v_m  = cv2.threshold(hsv[:, :, 2], 100, 255, cv2.THRESH_BINARY)[1]
    mask = cv2.bitwise_and(s_m, v_m)
    ker  = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, ker, iterations=6)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  ker, iterations=3)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    largest = max(cnts, key=cv2.contourArea)
    if cv2.contourArea(largest) < 0.12 * h * w:
        return None
    return cv2.boundingRect(largest)


# ── Helper: expand bounding box outward ──────────────────────────────────────

def _expand(x, y, bw, bh, margin, iw, ih):
    dx = int(bw * margin)
    dy = int(bh * margin)
    x2 = int(np.clip(x  - dx, 0, iw))
    y2 = int(np.clip(y  - dy, 0, ih))
    x3 = int(np.clip(x  + bw + dx, 0, iw))
    y3 = int(np.clip(y  + bh + dy, 0, ih))
    return x2, y2, x3 - x2, y3 - y2


# ── Public API ────────────────────────────────────────────────────────────────

def crop_slide(src_path, safety_margin=0.02, min_crop_ratio=0.15,
               max_crop_ratio=0.93):
    """
    Detect and crop the slide screen from a conference photo.

    Parameters
    ----------
    src_path       : str   — path to the original JPEG photo
    safety_margin  : float — expand detected region outward by this fraction
    min_crop_ratio : float — reject crop if < this fraction of original area
    max_crop_ratio : float — reject crop if > this fraction (no real detection)

    Returns PIL.Image (cropped), or a conservative fallback crop.
    """
    img_bgr = _imread(src_path)
    if img_bgr is None:
        return Image.open(src_path)

    ih, iw = img_bgr.shape[:2]
    img_area = ih * iw

    # ── 1. Pattern detection (primary, close-up shots) ────────────────────────
    # The projection detector now decides internally whether the blue side
    # panels are present; if they are not (wide-angle shot) it returns None and
    # we fall through to the blue-blob detector below.
    result = _detect_by_projection(img_bgr)
    if result is not None:
        x, y, bw, bh = result
        # Top is calibrated — never expand upward; expand sides and bottom only.
        dx = int(bw * safety_margin)
        dy = int(bh * safety_margin)
        x2  = max(0,  x - dx)
        y2  = y
        x3  = min(iw, x + bw + dx)
        y3  = min(ih, y + bh + dy)
        bw2, bh2 = x3 - x2, y3 - y2
        ratio = (bw2 * bh2) / img_area
        if min_crop_ratio < ratio < max_crop_ratio:
            cropped = img_bgr[y2:y3, x2:x3]
            if cropped.size > 0:
                return Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))

    # ── 2. CMAC blue-screen detector (wide-angle / rear-of-hall shots) ────────
    result = _detect_by_blue(img_bgr)
    if result is not None:
        x, y, bw, bh = _expand(*result, safety_margin, iw, ih)
        ratio = (bw * bh) / img_area
        if min_crop_ratio < ratio < max_crop_ratio:
            cropped = img_bgr[y:y+bh, x:x+bw]
            if cropped.size > 0:
                return Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))

    # ── 3. Generic brightness + saturation blob (fallback) ───────────────────
    result = _detect_by_hsv(img_bgr)
    if result is not None:
        x, y, bw, bh = _expand(*result, safety_margin, iw, ih)
        ratio = (bw * bh) / img_area
        if min_crop_ratio < ratio < max_crop_ratio:
            cropped = img_bgr[y:y+bh, x:x+bw]
            if cropped.size > 0:
                return Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))

    # ── 3. Conservative heuristic: strip audience + ceiling ──────────────────
    top_cut    = int(ih * 0.12)
    bottom_cut = int(ih * 0.20)
    cropped    = img_bgr[top_cut: ih - bottom_cut, 0:iw]
    if cropped.size > 0:
        return Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))

    return Image.open(src_path)


def crop_slide_to_bytesio(src_path, **kwargs):
    """Return a BytesIO PNG buffer (lossless, high quality) for python-pptx."""
    pil_img = crop_slide(src_path, **kwargs)
    buf = io.BytesIO()
    pil_img.save(buf, format='PNG')
    buf.seek(0)
    return buf, pil_img.size  # (BytesIO, (width_px, height_px))


# ══════════════════════════════════════════════════════════════════════════════
# Public API — content crop (v6, the one the skill should use)
# ══════════════════════════════════════════════════════════════════════════════

def crop_content(src_path, target_size=None):
    """
    Crop a conference photo down to the slide content (PPT info region):
    colored side frames, spotlight bar, and audience removed.

    Parameters
    ----------
    src_path    : str           — path to the original photo
    target_size : (w, h) | None — if given, the crop is resized (stretched) to
                                   exactly these pixels. Use this to force a set
                                   of photos to a UNIFORM size for tidy stacking
                                   (aspect ratio is intentionally not preserved).

    Returns a PIL.Image. Falls back to a conservative centre crop on failure.
    """
    img = _imread(src_path)
    if img is None:
        return Image.open(src_path)
    ih, iw = img.shape[:2]

    box = detect_content_region(img)
    if box is not None:
        L, T, R, B = box
        if (R - L) >= int(iw * 0.20) and (B - T) >= int(ih * 0.18):
            crop = img[T:B, L:R]
        else:
            crop = img[int(ih * 0.12): int(ih * 0.80), 0:iw]
    else:
        crop = img[int(ih * 0.12): int(ih * 0.80), 0:iw]

    pil = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
    if target_size is not None:
        pil = pil.resize(target_size, Image.LANCZOS)
    return pil


def crop_content_to_bytesio(src_path, **kwargs):
    """Return a (BytesIO PNG, (w, h)) for python-pptx, cropped to slide content."""
    pil_img = crop_content(src_path, **kwargs)
    buf = io.BytesIO()
    pil_img.save(buf, format='PNG')
    buf.seek(0)
    return buf, pil_img.size
