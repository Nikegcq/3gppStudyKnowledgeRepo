#!/usr/bin/env python3
"""Generate Excalidraw JSON for 38.211 Phase-1 frame structure diagrams."""
from __future__ import annotations

import json
import random
from pathlib import Path

OUT = Path(r"C:\Users\gaooocon\study\3gppStudyKnowledgeRepo\knowledgeRepo\30-Resources\3GPP规范")
OUT.mkdir(parents=True, exist_ok=True)

# palette
INK = "#1e1e1e"
MUTED = "#868e96"
BLUE = "#1971c2"
BLUE_BG = "#d0ebff"
CYAN = "#0c8599"
CYAN_BG = "#c5f6fa"
GREEN = "#2f9e44"
GREEN_BG = "#d3f9d8"
ORANGE = "#e8590c"
ORANGE_BG = "#ffe8cc"
PURPLE = "#6741d9"
PURGE_BG = "#e5dbff"
RED = "#e03131"
RED_BG = "#ffe3e3"
YELLOW = "#e67700"
YELLOW_BG = "#fff3bf"
GRAY_BG = "#f1f3f5"
BORDER = "#495057"

_seed = 1000


def sid() -> str:
    global _seed
    _seed += 1
    return f"el{_seed:04d}"


def base(x, y, w, h, **kw):
    el = {
        "id": sid(),
        "type": "rectangle",
        "x": float(x),
        "y": float(y),
        "width": float(w),
        "height": float(h),
        "angle": 0,
        "strokeColor": kw.get("strokeColor", INK),
        "backgroundColor": kw.get("backgroundColor", "transparent"),
        "fillStyle": kw.get("fillStyle", "solid"),
        "strokeWidth": kw.get("strokeWidth", 1),
        "strokeStyle": kw.get("strokeStyle", "solid"),
        "roughness": kw.get("roughness", 0),
        "opacity": 100,
        "groupIds": kw.get("groupIds", []),
        "frameId": None,
        "roundness": kw.get("roundness", {"type": 3}),
        "seed": random.randint(1, 1_000_000),
        "version": 1,
        "versionNonce": random.randint(1, 1_000_000),
        "isDeleted": False,
        "boundElements": None,
        "updated": 1,
        "link": None,
        "locked": False,
    }
    if kw.get("type"):
        el["type"] = kw["type"]
    if el["type"] == "line":
        el["points"] = kw["points"]
        el["lastCommittedPoint"] = None
        el["startBinding"] = None
        el["endBinding"] = None
        el["startArrowhead"] = kw.get("startArrowhead")
        el["endArrowhead"] = kw.get("endArrowhead", "arrow")
        el["roundness"] = {"type": 2}
    if el["type"] == "arrow":
        el["points"] = kw["points"]
        el["lastCommittedPoint"] = None
        el["startBinding"] = None
        el["endBinding"] = None
        el["startArrowhead"] = kw.get("startArrowhead")
        el["endArrowhead"] = kw.get("endArrowhead", "arrow")
        el["roundness"] = {"type": 2}
    return el


def rect(x, y, w, h, bg="transparent", stroke=INK, group=None, sw=1, style="solid"):
    return base(
        x, y, w, h,
        backgroundColor=bg,
        strokeColor=stroke,
        groupIds=[group] if group else [],
        strokeWidth=sw,
        strokeStyle=style,
    )


def text(x, y, s, size=16, color=INK, align="left", group=None, w=None, h=None):
    # approximate width for CJK ~ size, latin ~ size*0.55
    if w is None:
        w = sum(size if ord(c) > 127 else size * 0.55 for c in s) + 4
    if h is None:
        h = size * 1.25
    return {
        "id": sid(),
        "type": "text",
        "x": float(x),
        "y": float(y),
        "width": float(w),
        "height": float(h),
        "angle": 0,
        "strokeColor": color,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "groupIds": [group] if group else [],
        "frameId": None,
        "roundness": None,
        "seed": random.randint(1, 1_000_000),
        "version": 1,
        "versionNonce": random.randint(1, 1_000_000),
        "isDeleted": False,
        "boundElements": None,
        "updated": 1,
        "link": None,
        "locked": False,
        "text": s,
        "fontSize": size,
        "fontFamily": 1,
        "textAlign": align,
        "verticalAlign": "top",
        "containerId": None,
        "originalText": s,
        "lineHeight": 1.25,
        "baseline": size,
    }


def arrow(x1, y1, x2, y2, color=INK, group=None, sw=1, head="arrow"):
    return base(
        x1, y1, abs(x2 - x1) or 0.01, abs(y2 - y1) or 0.01,
        type="arrow",
        points=[[0, 0], [x2 - x1, y2 - y1]],
        strokeColor=color,
        groupIds=[group] if group else [],
        strokeWidth=sw,
        endArrowhead=head,
    )


def line(x1, y1, x2, y2, color=INK, group=None, sw=1, style="solid"):
    return base(
        x1, y1, abs(x2 - x1) or 0.01, abs(y2 - y1) or 0.01,
        type="line",
        points=[[0, 0], [x2 - x1, y2 - y1]],
        strokeColor=color,
        groupIds=[group] if group else [],
        strokeWidth=sw,
        strokeStyle=style,
        endArrowhead=None,
    )


def write(name: str, elements: list, bg="#ffffff"):
    path = OUT / name
    payload = {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {
            "gridSize": 20,
            "gridStep": 5,
            "gridModeEnabled": False,
            "viewBackgroundColor": bg,
        },
        "files": {},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {path} ({len(elements)} elements)")


# ---------------------------------------------------------------------------
# Diagram 1: Frame hierarchy overview
# ---------------------------------------------------------------------------
def diagram_frame_hierarchy():
    els = []
    els.append(text(40, 20, "38.211 阶段1 · NR 帧结构层级", 28, INK))
    els.append(text(40, 56, "Radio Frame → Half-frame → Subframe → Slot → OFDM Symbol（子帧恒 1 ms）", 14, MUTED))

    # Radio frame bar
    y0 = 110
    els.append(rect(40, y0, 900, 48, bg=BLUE_BG, stroke=BLUE, sw=2))
    els.append(text(60, y0 + 14, "无线帧 Radio Frame = 10 ms", 18, BLUE))
    els.append(text(700, y0 + 16, "n_f 帧号", 14, MUTED))

    # two half frames
    y1 = y0 + 80
    els.append(rect(40, y1, 430, 40, bg=CYAN_BG, stroke=CYAN))
    els.append(text(55, y1 + 10, "半帧 0 = 5 ms（子帧 0–4）", 16, CYAN))
    els.append(rect(510, y1, 430, 40, bg=CYAN_BG, stroke=CYAN))
    els.append(text(525, y1 + 10, "半帧 1 = 5 ms（子帧 5–9）", 16, CYAN))
    els.append(arrow(300, y0 + 48, 250, y1, MUTED))
    els.append(arrow(680, y0 + 48, 730, y1, MUTED))

    # 10 subframes
    y2 = y1 + 70
    sf_w = 88
    sf_gap = 2
    els.append(text(40, y2 - 22, "子帧 Subframe（恒 1 ms）· 每帧 10 个 · 编号 0–9", 14, MUTED))
    for i in range(10):
        x = 40 + i * (sf_w + sf_gap)
        bg = GREEN_BG if i < 5 else YELLOW_BG
        stroke = GREEN if i < 5 else YELLOW
        els.append(rect(x, y2, sf_w, 36, bg=bg, stroke=stroke))
        els.append(text(x + 28, y2 + 10, f"SF{i}", 14, stroke))

    # expand SF0 into slots
    y3 = y2 + 70
    els.append(arrow(84, y2 + 36, 84, y3 - 4, MUTED, head="arrow"))
    els.append(text(100, y3 - 18, "以子帧 0 为例（时隙数随 numerology μ 变化）", 14, MUTED))

    # three numerology rows
    rows = [
        ("μ=0  Δf=15 kHz", 1, "1 时隙 × 14 符号 · 时隙时长 1 ms", GREEN),
        ("μ=1  Δf=30 kHz", 2, "2 时隙 × 14 符号 · 时隙时长 0.5 ms", CYAN),
        ("μ=2  Δf=60 kHz", 4, "4 时隙 × 14 符号 · 时隙时长 0.25 ms", BLUE),
    ]
    for r, (label, nslots, note, color) in enumerate(rows):
        yy = y3 + r * 70
        els.append(text(40, yy, label, 16, color))
        els.append(text(220, yy + 2, note, 13, MUTED))
        bar_x, bar_w = 40, 700
        slot_w = bar_w / nslots
        for s in range(nslots):
            sx = bar_x + s * slot_w
            els.append(rect(sx, yy + 24, slot_w - 2, 32, bg=GRAY_BG, stroke=color))
            els.append(text(sx + 8, yy + 32, f"Slot {s}", 12, color))
            # 14 tick symbols
            if r == 0 or s == 0:
                tick_y = yy + 56
                for sym in range(14):
                    tx = sx + 4 + sym * (slot_w - 10) / 14
                    els.append(line(tx, tick_y, tx, tick_y + 8, color=MUTED, sw=1))
                if r == 0:
                    els.append(text(bar_x, tick_y + 12, "OFDM 符号 l = 0 … 13（Normal CP，14 个/时隙）", 12, MUTED))

    # Extended CP note
    y_ext = y3 + 3 * 70 + 10
    els.append(rect(40, y_ext, 700, 36, bg=ORANGE_BG, stroke=ORANGE, style="dashed"))
    els.append(text(55, y_ext + 10, "Extended CP：仅 μ=2（60 kHz）可用 · 每时隙 12 符号", 14, ORANGE))

    # key formulas
    y_k = y_ext + 60
    els.append(text(40, y_k, "关键关系（38.211 §4.2 / §4.3）", 16, INK))
    formulas = [
        "Δf = 15 × 2^μ kHz",
        "时隙数/子帧 = 2^μ  ·  时隙数/帧 = 10 × 2^μ",
        "符号数/时隙 = 14（Normal CP）/ 12（Extended，仅 μ=2）",
        "子帧恒 1 ms；只有 μ=0 时 1 子帧 = 1 时隙",
    ]
    for i, f in enumerate(formulas):
        els.append(text(50, y_k + 28 + i * 22, "•  " + f, 13, MUTED))

    els.append(text(40, y_k + 140, "来源：学习-38.211-阶段1-帧结构与时频资源 · TS 38.211 v19.4.0 §4.3", 12, MUTED))
    write("图-38.211-阶段1-帧结构总览.excalidraw", els)


# ---------------------------------------------------------------------------
# Diagram 2: Resource grid / Point A / CRB / PRB / BWP  (clear positions)
# ---------------------------------------------------------------------------
def draw_bracket_v(els, x, y_top, y_bot, color, label, sub=None, side="left"):
    """Vertical bracket with label. side=left: arm to the left of x."""
    arm = 18
    els.append(line(x, y_top, x - arm, y_top, color=color, sw=2))
    els.append(line(x - arm, y_top, x - arm, y_bot, color=color, sw=2))
    els.append(line(x - arm, y_bot, x, y_bot, color=color, sw=2))
    mid = (y_top + y_bot) / 2
    els.append(text(x - arm - 110, mid - 12, label, 14, color))
    if sub:
        els.append(text(x - arm - 110, mid + 6, sub, 11, MUTED))


def diagram_resource_grid():
    els = []
    els.append(text(40, 16, "38.211 §4.4 · 资源网格位置图：RB / CRB / PRB / BWP / Point A", 24, INK))
    els.append(text(40, 48, "频域向上增大 · 每个 RB = 12 个连续子载波 · CRB 从 Point A 起全网编号 · PRB 在 BWP 内从 0 编号", 13, MUTED))

    # ===== layout constants =====
    n_rb = 5                 # show 5 RBs
    n_sc = 12                # subcarriers per RB
    n_sym = 6                # symbols shown (of 14)
    cell_w = 78              # symbol width
    cell_h = 14              # subcarrier height
    grid_x = 280             # left edge of grid cells
    grid_y = 140             # top of highest RB

    grid_w = n_sym * cell_w
    rb_h = n_sc * cell_h     # 168
    grid_h = n_rb * rb_h
    # example: BWP starts at CRB 30, covers CRB 30..34 (PRB 0..4)
    n_bwp_start = 30

    # color per RB (top to bottom = high freq to low freq)
    colors_bg = [BLUE_BG, CYAN_BG, GREEN_BG, YELLOW_BG, ORANGE_BG]
    colors_st = [BLUE, CYAN, GREEN, YELLOW, ORANGE]

    # ---- time axis header ----
    for l in range(n_sym):
        x = grid_x + l * cell_w
        els.append(rect(x, grid_y - 32, cell_w - 2, 26, bg=GRAY_BG, stroke=MUTED))
        els.append(text(x + 22, grid_y - 27, f"l={l}", 13, MUTED))
    els.append(text(grid_x + grid_w + 8, grid_y - 27, "… l=13（共 14 符号）", 12, MUTED))
    els.append(text(grid_x + grid_w / 2 - 40, grid_y - 56, "时间 →", 13, INK))

    # ---- draw RB bands (rb index 0 = highest frequency) ----
    for i in range(n_rb):
        y = grid_y + i * rb_h
        # CRB / PRB numbers: bottom-most drawn RB is lowest freq among the 5
        # i=0 top → highest CRB; i=n_rb-1 bottom → lowest CRB = n_bwp_start
        prb = (n_rb - 1) - i
        crb = n_bwp_start + prb
        # thick RB separator line between bands
        if i > 0:
            els.append(line(grid_x - 4, y, grid_x + grid_w, y, color=colors_st[i], sw=2))
        for sc in range(n_sc):
            yy = y + sc * cell_h
            for l in range(n_sym):
                x = grid_x + l * cell_w
                els.append(rect(
                    x, yy, cell_w - 1, cell_h - 1,
                    bg=colors_bg[i], stroke="#adb5bd", sw=0.5,
                ))
        # inside-grid CRB/PRB tag on first column
        els.append(text(grid_x + 8, y + 6, f"PRB {prb}", 12, colors_st[i]))
        els.append(text(grid_x + 8, y + 22, f"CRB {crb}", 12, colors_st[i]))

        # left vertical brace for this RB
        bx = grid_x - 8
        els.append(line(bx, y, bx - 12, y, color=colors_st[i], sw=2))
        els.append(line(bx - 12, y, bx - 12, y + rb_h, color=colors_st[i], sw=2))
        els.append(line(bx - 12, y + rb_h, bx, y + rb_h, color=colors_st[i], sw=2))
        els.append(text(bx - 120, y + rb_h / 2 - 22, f"RB/CRB {crb}", 13, colors_st[i]))
        els.append(text(bx - 120, y + rb_h / 2 - 4, "= PRB %d" % prb, 12, MUTED))
        els.append(text(bx - 120, y + rb_h / 2 + 12, "12 子载波", 11, MUTED))

    # ---- subcarrier tick marks on the left of bottom RB (show k) ----
    bottom_y = grid_y + (n_rb - 1) * rb_h
    for sc in range(n_sc):
        yy = bottom_y + sc * cell_h + cell_h / 2
        els.append(line(grid_x - 4, yy, grid_x + 4, yy, color=MUTED, sw=1))
    els.append(text(grid_x - 160, bottom_y + rb_h + 8, "↑ 每格 = 1 个子载波（RE 的频域）", 11, MUTED))

    # ---- BWP bracket on the far left spanning all drawn RBs ----
    bwp_x = 48
    bwp_top = grid_y
    bwp_bot = grid_y + grid_h
    els.append(rect(bwp_x, bwp_top, 10, grid_h, bg=PURPLE, stroke=PURPLE, sw=2))
    els.append(line(bwp_x + 10, bwp_top, bwp_x + 28, bwp_top, color=PURPLE, sw=2))
    els.append(line(bwp_x + 10, bwp_bot, bwp_x + 28, bwp_bot, color=PURPLE, sw=2))
    els.append(text(bwp_x - 4, bwp_top - 28, "BWP", 18, PURPLE))
    els.append(text(bwp_x - 4, bwp_bot + 10, "连续 5 个 CRB", 12, PURPLE))
    els.append(text(bwp_x - 4, bwp_bot + 28, "N_BWP,start = 30", 12, PURPLE))
    # callout arrow from BWP label to bar
    els.append(arrow(bwp_x + 40, bwp_top - 10, bwp_x + 5, bwp_top + 40, color=PURPLE))

    # ---- Point A at bottom (below lowest CRB) ----
    pa_y = bwp_bot + 56
    els.append(line(40, pa_y, grid_x + grid_w + 40, pa_y, color=RED, sw=2, style="dashed"))
    els.append(text(40, pa_y + 10, "Point A  =  CRB0 的子载波 0 中心（频率零点，所有 μ 共用）", 13, RED))
    els.append(text(40, pa_y + 30, "本图画的是 BWP 内的 CRB 30–34，更低频还有 CRB 0–29 → 方向 Point A", 12, MUTED))
    # upward frequency arrow on Point A side
    els.append(arrow(200, pa_y - 8, 200, grid_y + 40, color=RED, head="arrow"))
    els.append(text(210, (pa_y + grid_y) / 2, "频率 k ↑", 13, RED))

    # ---- highlight one RE ----
    re_l, re_sc_in_rb = 2, 3
    re_x = grid_x + re_l * cell_w
    re_y = grid_y + 1 * rb_h + re_sc_in_rb * cell_h   # inside second band from top
    els.append(rect(re_x, re_y, cell_w - 1, cell_h - 1, bg=RED_BG, stroke=RED, sw=3))
    els.append(arrow(re_x + 30, re_y - 50, re_x + 30, re_y - 2, color=RED, sw=2))
    els.append(text(re_x + 8, re_y - 78, "RE(k, l)", 14, RED))
    els.append(text(re_x + 8, re_y - 60, "网格最小单元", 11, MUTED))

    # ---- right side: legend + formula ----
    px, py = 980, 100
    els.append(rect(px, py, 300, 520, bg=GRAY_BG, stroke=MUTED))
    els.append(text(px + 16, py + 14, "位置怎么读", 18, INK))
    lines = [
        ("RB", "12 个连续子载波（数量恒定）", GREEN),
        ("RB 频宽", "12 × Δf，随 μ 变化", GREEN),
        ("CRB n", "从 Point A 起的第 n 个 RB", BLUE),
        ("", "n_CRB = ⌊k / 12⌋", BLUE),
        ("PRB n", "BWP 内从 0 起的第 n 个 RB", CYAN),
        ("", "n_CRB = n_PRB + N_BWP,start", CYAN),
        ("BWP", "同一 numerology 下连续 CRB", PURPLE),
        ("", "PRB0 就是 CRB N_BWP,start", PURPLE),
        ("Point A", "公共频率零点 / CRB0 原点", RED),
        ("RE(k,l)", "子载波 k × 符号 l 的一格", RED),
    ]
    yy = py + 48
    for a, b, c in lines:
        if a:
            els.append(text(px + 16, yy, a, 13, c))
            yy += 18
            els.append(text(px + 28, yy, b, 12, MUTED))
        else:
            els.append(text(px + 28, yy, b, 12, c))
        yy += 22

    els.append(text(px + 16, py + 400, "本图数值示例", 14, INK))
    els.append(text(px + 16, py + 424, "BWP: CRB 30–34 = PRB 0–4", 12, MUTED))
    els.append(text(px + 16, py + 444, "N_BWP,start = 30", 12, MUTED))
    els.append(text(px + 16, py + 464, "载波再往外才是 guardband", 12, MUTED))

    els.append(text(40, pa_y + 70, "来源：TS 38.211 §4.4.3–4.4.5 · 学习-38.211-阶段1-帧结构与时频资源", 12, MUTED))
    write("图-38.211-阶段1-资源网格-RE-RB-BWP.excalidraw", els)


# ---------------------------------------------------------------------------
# Diagram 3: Channel bandwidth vs transmission bandwidth
# ---------------------------------------------------------------------------
def diagram_channel_bw():
    els = []
    els.append(text(40, 20, "38.104 阶段1配套 · 信道带宽 ≠ 传输带宽", 26, INK))
    els.append(text(40, 54, "例：FR1 · 20 MHz 信道带宽 · SCS 30 kHz → 传输带宽 51 RB（约 18.36 MHz）+ 两侧保护带", 14, MUTED))

    # Channel bandwidth bar
    y0 = 140
    els.append(rect(60, y0, 900, 56, bg=GRAY_BG, stroke=INK, sw=2))
    els.append(text(380, y0 + 18, "信道带宽 Channel Bandwidth = 20 MHz", 16, INK))

    # Guard bands + transmission
    # approximate proportions: 51*12*30e3 = 18.36e6 → 91.8% of 20MHz
    total_w = 900
    tx_ratio = 18.36 / 20.0
    tx_w = total_w * tx_ratio
    gb_w = (total_w - tx_w) / 2
    y1 = y0 + 80
    els.append(rect(60, y1, gb_w, 48, bg=YELLOW_BG, stroke=YELLOW))
    els.append(text(60 + gb_w / 2 - 40, y1 + 16, "保护带", 13, YELLOW))
    els.append(rect(60 + gb_w, y1, tx_w, 48, bg=BLUE_BG, stroke=BLUE, sw=2))
    els.append(text(60 + gb_w + tx_w / 2 - 90, y1 + 14, "传输带宽 = 51 RB × 12 × 30 kHz", 14, BLUE))
    els.append(text(60 + gb_w + tx_w / 2 - 50, y1 + 32, "≈ 18.36 MHz", 12, BLUE))
    els.append(rect(60 + gb_w + tx_w, y1, gb_w, 48, bg=YELLOW_BG, stroke=YELLOW))
    els.append(text(60 + gb_w + tx_w + gb_w / 2 - 40, y1 + 16, "保护带", 13, YELLOW))

    # Brackets
    els.append(line(60, y0 + 60, 960, y0 + 60, color=INK, sw=1))
    els.append(text(460, y0 + 66, "20 MHz", 12, INK))

    # Numbers panel
    y2 = 280
    els.append(rect(60, y2, 420, 200, bg=GRAY_BG, stroke=MUTED))
    els.append(text(80, y2 + 16, "验算（38.104 Table 5.3.2-1）", 16, INK))
    calc = [
        "信道带宽：20 MHz",
        "SCS：30 kHz（μ=1）",
        "传输带宽配置：51 RB",
        "占用：51 × 12 × 30 kHz = 18.36 MHz",
        "保护带合计：20 − 18.36 = 1.64 MHz",
        "两侧约各 0.82 MHz",
    ]
    for i, s in enumerate(calc):
        els.append(text(80, y2 + 48 + i * 22, "•  " + s, 13, MUTED))

    els.append(rect(520, y2, 440, 200, bg=ORANGE_BG, stroke=ORANGE))
    els.append(text(540, y2 + 16, "频段速查（38.104 §5）", 16, ORANGE))
    bands = [
        "FR1：410 – 7125 MHz（15/30/60 kHz 为主）",
        "FR2-1：24.25 – 52.6 GHz（60/120 kHz）",
        "FR2-2：52.6 – 71 GHz（120/480/960 kHz，R18）",
        "RB 数随 SCS / 信道带宽查表，不是固定值",
    ]
    for i, s in enumerate(bands):
        els.append(text(540, y2 + 48 + i * 22, "•  " + s, 13, ORANGE))

    els.append(text(60, 520, "易错：DCI 调度的 PRB 编号是 BWP 内相对编号，不是绝对 CRB，也不是信道带宽边缘。", 13, RED))
    els.append(text(60, 546, "来源：TS 38.104 §5.3 · 学习-38.211-阶段1 §5", 12, MUTED))
    write("图-38.211-阶段1-信道带宽与传输带宽.excalidraw", els)


# ---------------------------------------------------------------------------
# Diagram 4: Hand-practice answers (practice 2 has clear CRB/PRB/BWP positions)
# ---------------------------------------------------------------------------
def diagram_practice_answers():
    els = []
    els.append(text(40, 16, "手画练习答案 · 38.211 阶段1（对照笔记 §6）", 26, INK))
    els.append(text(40, 50, "练习1 Numerology 时间轴 · 练习2 资源网格 CRB/PRB/BWP 位置 · 练习3 20 MHz 带宽验算", 14, MUTED))

    # ---- Practice 1 ----
    y = 100
    els.append(rect(40, y, 1000, 36, bg=BLUE_BG, stroke=BLUE))
    els.append(text(55, y + 8, "练习 1 答案：1 ms 子帧内 μ=0/1/2 的时隙与符号（Normal CP）", 16, BLUE))

    rows = [
        ("μ=0", 1, "1 ms", "14 符号", GREEN),
        ("μ=1", 2, "0.5 ms", "14 符号/时隙", CYAN),
        ("μ=2", 4, "0.25 ms", "14 符号/时隙", BLUE),
    ]
    y_r = y + 50
    bar_x, bar_w = 120, 720
    for r, (lab, n, slotdur, nsym, color) in enumerate(rows):
        yy = y_r + r * 72
        els.append(text(50, yy + 16, lab, 16, color))
        els.append(text(50, yy + 36, f"Δf={15*(2**r)}k", 11, MUTED))
        for s in range(n):
            sx = bar_x + s * (bar_w / n)
            sw = bar_w / n - 2
            els.append(rect(sx, yy, sw, 40, bg=GRAY_BG, stroke=color, sw=2))
            els.append(text(sx + 10, yy + 6, f"Slot {s}", 13, color))
            els.append(text(sx + 10, yy + 22, slotdur, 11, MUTED))
            for sym in range(14):
                tx = sx + 6 + sym * (sw - 12) / 14
                els.append(line(tx, yy + 40, tx, yy + 50, color=color, sw=1))
        els.append(text(bar_x + bar_w + 12, yy + 12, f"{n} 时隙 · {nsym}", 12, color))

    y_e = y_r + 3 * 72
    els.append(text(50, y_e + 8, "μ=2 Ext", 14, ORANGE))
    for s in range(4):
        sx = bar_x + s * (bar_w / 4)
        sw = bar_w / 4 - 2
        els.append(rect(sx, y_e, sw, 40, bg=ORANGE_BG, stroke=ORANGE, sw=2, style="dashed"))
        els.append(text(sx + 10, y_e + 6, f"Slot {s}", 13, ORANGE))
        els.append(text(sx + 10, y_e + 22, "12 符号", 11, ORANGE))
    els.append(text(bar_x + bar_w + 12, y_e + 12, "Extended CP 仅 μ=2", 12, ORANGE))

    # ---- Practice 2: LARGE clear CRB / PRB / BWP position map ----
    y2 = y_e + 90
    els.append(rect(40, y2, 1000, 36, bg=GREEN_BG, stroke=GREEN))
    els.append(text(55, y2 + 8, "练习 2 答案：CRB / PRB / BWP 位置标注（频域向上，Point A 在最下）", 16, GREEN))

    # grid params
    n_rb = 4
    n_sc = 12
    n_sym = 5
    cell_w = 72
    cell_h = 12
    gx = 300
    gy = y2 + 70
    rb_h = n_sc * cell_h
    grid_h = n_rb * rb_h
    grid_w = n_sym * cell_w
    n_bwp_start = 20   # PRB0 = CRB 20

    # symbol header
    for l in range(n_sym):
        x = gx + l * cell_w
        els.append(rect(x, gy - 28, cell_w - 2, 22, bg=GRAY_BG, stroke=MUTED))
        els.append(text(x + 20, gy - 25, f"l={l}", 12, MUTED))
    els.append(text(gx + grid_w + 6, gy - 25, "… l=13", 12, MUTED))

    colors_bg = [BLUE_BG, CYAN_BG, GREEN_BG, YELLOW_BG]
    colors_st = [BLUE, CYAN, GREEN, YELLOW]

    for i in range(n_rb):
        ytop = gy + i * rb_h
        prb = (n_rb - 1) - i
        crb = n_bwp_start + prb
        if i > 0:
            els.append(line(gx, ytop, gx + grid_w, ytop, color=colors_st[i], sw=2))
        for sc in range(n_sc):
            yy = ytop + sc * cell_h
            for l in range(n_sym):
                x = gx + l * cell_w
                els.append(rect(x, yy, cell_w - 1, cell_h - 1, bg=colors_bg[i], stroke="#adb5bd", sw=0.5))
        # label inside
        els.append(text(gx + 10, ytop + 8, f"PRB {prb}", 13, colors_st[i]))
        els.append(text(gx + 10, ytop + 26, f"CRB {crb}", 13, colors_st[i]))

        # left brace + labels
        bx = gx - 6
        els.append(line(bx, ytop, bx - 14, ytop, color=colors_st[i], sw=2))
        els.append(line(bx - 14, ytop, bx - 14, ytop + rb_h, color=colors_st[i], sw=2))
        els.append(line(bx - 14, ytop + rb_h, bx, ytop + rb_h, color=colors_st[i], sw=2))
        mid = ytop + rb_h / 2
        els.append(text(bx - 150, mid - 24, f"CRB {crb}", 14, colors_st[i]))
        els.append(text(bx - 150, mid - 4, f"PRB {prb}", 14, MUTED))
        els.append(text(bx - 150, mid + 14, "RB = 12×Δf", 11, MUTED))

    # BWP thick bar far left
    bwp_x = 56
    els.append(rect(bwp_x, gy, 12, grid_h, bg=PURPLE, stroke=PURPLE, sw=2))
    els.append(line(bwp_x + 12, gy, bwp_x + 30, gy, color=PURPLE, sw=2))
    els.append(line(bwp_x + 12, gy + grid_h, bwp_x + 30, gy + grid_h, color=PURPLE, sw=2))
    els.append(text(bwp_x - 8, gy - 30, "BWP", 18, PURPLE))
    els.append(text(bwp_x - 8, gy + grid_h + 12, "CRB 20–23", 12, PURPLE))
    els.append(text(bwp_x - 8, gy + grid_h + 28, "= PRB 0–3", 12, PURPLE))
    els.append(text(bwp_x - 8, gy + grid_h + 44, "N_BWP,start=20", 12, PURPLE))

    # Point A
    pa_y = gy + grid_h + 70
    els.append(line(40, pa_y, gx + grid_w + 40, pa_y, color=RED, sw=2, style="dashed"))
    els.append(text(40, pa_y + 10, "Point A（CRB0 子载波0 中心）← 方向：更低频还有 CRB 0–19", 13, RED))

    # frequency arrow
    els.append(arrow(230, pa_y - 6, 230, gy + 30, color=RED, head="arrow"))
    els.append(text(238, (gy + pa_y) / 2, "频率 k↑", 12, RED))

    # RE highlight
    re_x = gx + 2 * cell_w
    re_y = gy + 1 * rb_h + 4 * cell_h
    els.append(rect(re_x, re_y, cell_w - 1, cell_h - 1, bg=RED_BG, stroke=RED, sw=3))
    els.append(text(re_x + cell_w + 8, re_y - 8, "RE(k,l)", 12, RED))

    # formula box
    fx, fy = 780, y2 + 70
    els.append(rect(fx, fy, 280, 200, bg=GRAY_BG, stroke=MUTED))
    els.append(text(fx + 14, fy + 12, "核对公式", 16, INK))
    formulas = [
        "n_CRB = n_PRB + N_BWP,start",
        "PRB0 = CRB 20",
        "PRB1 = CRB 21",
        "PRB2 = CRB 22",
        "PRB3 = CRB 23",
        "RB 恒 12 子载波",
    ]
    for i, s in enumerate(formulas):
        els.append(text(fx + 14, fy + 40 + i * 22, "•  " + s, 12, MUTED))

    # ---- Practice 3 ----
    y3 = pa_y + 50
    els.append(rect(40, y3, 1000, 36, bg=ORANGE_BG, stroke=ORANGE))
    els.append(text(55, y3 + 8, "练习 3 答案：20 MHz / 30 kHz → 51 RB（38.104 Table 5.3.2-1）", 16, ORANGE))

    y4 = y3 + 50
    tx_w = 860 * (18.36 / 20)
    gb_w = (860 - tx_w) / 2
    els.append(rect(60, y4, 860, 44, bg=GRAY_BG, stroke=INK, sw=2))
    els.append(rect(60, y4, gb_w, 44, bg=YELLOW_BG, stroke=YELLOW))
    els.append(rect(60 + gb_w, y4, tx_w, 44, bg=BLUE_BG, stroke=BLUE))
    els.append(rect(60 + gb_w + tx_w, y4, gb_w, 44, bg=YELLOW_BG, stroke=YELLOW))
    els.append(text(60 + gb_w + tx_w / 2 - 110, y4 + 12, "51 RB = 18.36 MHz", 14, BLUE))
    els.append(text(80, y4 + 12, "GB", 12, YELLOW))
    els.append(text(840, y4 + 12, "GB", 12, YELLOW))

    ans = [
        "占用带宽 = 51 × 12 × 30 kHz = 18.36 MHz",
        "保护带合计 = 20 − 18.36 = 1.64 MHz（两侧）",
        "结论：信道带宽包含传输带宽 + 保护带；RB 数必须查表。",
    ]
    for i, s in enumerate(ans):
        els.append(text(60, y4 + 60 + i * 22, "•  " + s, 13, INK))

    els.append(text(40, y4 + 140, "对照笔记：[[学习-38.211-阶段1-帧结构与时频资源]] · 规范：TS 38.211 §4 · TS 38.104 §5.3", 12, MUTED))
    write("图-38.211-阶段1-手画练习答案.excalidraw", els)


# ---------------------------------------------------------------------------
# Diagram 5: Timeline units Tc / Ts quick ref (optional compact)
# ---------------------------------------------------------------------------
def diagram_time_units():
    els = []
    els.append(text(40, 20, "NR 时间单位：T_c 与 T_s（38.211 §4.1）", 24, INK))
    els.append(text(40, 52, "所有帧/子帧/符号边界都是 T_c 的整数倍；κ = T_s / T_c = 64 可从 LTE 换算", 14, MUTED))

    boxes = [
        (40, 110, 280, 100, BLUE_BG, BLUE, "T_c ≈ 0.509 ns", "基本时间单位\n1/(480 kHz × 4096)"),
        (360, 110, 280, 100, CYAN_BG, CYAN, "T_s ≈ 32.55 ns", "LTE 采样周期\n1/(15 kHz × 2048)"),
        (680, 110, 280, 100, GREEN_BG, GREEN, "κ = 64", "T_s = 64 × T_c"),
    ]
    for x, y, w, h, bg, stroke, title, sub in boxes:
        els.append(rect(x, y, w, h, bg=bg, stroke=stroke, sw=2))
        els.append(text(x + 16, y + 16, title, 18, stroke))
        for i, line in enumerate(sub.split("\n")):
            els.append(text(x + 16, y + 48 + i * 20, line, 13, MUTED))

    els.append(arrow(320, 160, 360, 160, MUTED))
    els.append(arrow(640, 160, 680, 160, MUTED))

    # hierarchy duration
    y = 260
    items = [
        ("无线帧", "10 ms"),
        ("半帧", "5 ms"),
        ("子帧", "1 ms"),
        ("时隙 μ=0", "1 ms"),
        ("时隙 μ=1", "0.5 ms"),
        ("时隙 μ=2", "0.25 ms"),
        ("符号 μ=0", "≈ 66.7 μs + CP"),
    ]
    els.append(text(40, y, "持续时间速查", 16, INK))
    for i, (a, b) in enumerate(items):
        yy = y + 30 + i * 28
        els.append(rect(40, yy, 160, 24, bg=GRAY_BG, stroke=MUTED))
        els.append(text(52, yy + 4, a, 13, INK))
        els.append(rect(210, yy, 160, 24, bg=BLUE_BG, stroke=BLUE))
        els.append(text(222, yy + 4, b, 13, BLUE))

    els.append(rect(420, y, 500, 220, bg=ORANGE_BG, stroke=ORANGE))
    els.append(text(440, y + 16, "为何要记 T_c？", 16, ORANGE))
    notes = [
        "• 规范里所有时长写成 N × T_c，不是直接写微秒",
        "• 帧号相同 ≠ 物理时间对齐：UL 有 TA 提前",
        "• T_TA = (N_TA + …) × T_c，见 38.213 §4.2",
        "• 与 LTE 对比时用 κ=64 做 Ts ↔ Tc 换算",
    ]
    for i, s in enumerate(notes):
        els.append(text(440, y + 48 + i * 24, s, 13, ORANGE))

    els.append(text(40, 520, "来源：概念-NR时间单位-Tc与Ts · 38.211 §4.1", 12, MUTED))
    write("图-38.211-阶段1-时间单位-Tc-Ts.excalidraw", els)


if __name__ == "__main__":
    random.seed(42)
    diagram_frame_hierarchy()
    diagram_resource_grid()
    diagram_channel_bw()
    diagram_practice_answers()
    diagram_time_units()
    print("done")
