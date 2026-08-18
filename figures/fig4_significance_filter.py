from svgkit import BODY, LINE_H, SEC, Line, Svg, box_width_for, measure, wrap

M = 30
PAD = 16
PAD_V = 18
SEC_FILL = "#4d4d4d"
BULLET = "•  "


def box_h_for(n_lines: int) -> float:
    return LINE_H * (n_lines - 1) + 2 * PAD_V


def text_block(s: Svg, x: float, top: float, lines: list[Line], anchor: str = "start") -> None:
    for i, ln in enumerate(lines):
        baseline = top + i * LINE_H + 0.36 * ln.size
        s.text(x, baseline, ln.text, ln.size, ln.bold, anchor, ln.fill)


# --- left chain ---------------------------------------------------------
CHAIN_LABELS = [
    ("Candidate dispatch sites", "grey", None),
    ("Damp high fan-in helpers", "white", None),
    ("Compute arm reach", "white", None),
    ("Classify each arm", "white", "guard / void / live"),
]
BOX_H = box_h_for(2)
CHAIN_GAP = 24
CHAIN_TOP = 50
CHAIN_X = M
CHAIN_W = box_width_for(
    [(t, BODY, False) for t, _, _ in CHAIN_LABELS]
    + [(sub, SEC, False) for _, _, sub in CHAIN_LABELS if sub],
    pad=PAD,
)
chain_y = [CHAIN_TOP + i * (BOX_H + CHAIN_GAP) for i in range(len(CHAIN_LABELS))]
chain_bottom = chain_y[-1] + BOX_H
chain_cx = CHAIN_X + CHAIN_W / 2

# --- middle panel ---------------------------------------------------------
BULLETS = [
    "log of live reach union",
    "provenance of tested value",
    "arms fail to reconverge",
    "route, table, polymorphic bonus",
]
PANEL_HEAD = "Four-term score"
PANEL_ROWS = 1 + len(BULLETS)
PANEL_H = LINE_H * PANEL_ROWS + 2 * PAD
PANEL_W = box_width_for(
    [(PANEL_HEAD, BODY, True)] + [(BULLET + b, BODY, False) for b in BULLETS], pad=PAD
)
CORRIDOR = 70
PANEL_X = CHAIN_X + CHAIN_W + CORRIDOR
LANE_X = CHAIN_X + CHAIN_W + CORRIDOR / 2
Y_MID = (CHAIN_TOP + chain_bottom) / 2
PANEL_Y = Y_MID - PANEL_H / 2
panel_cx = PANEL_X + PANEL_W / 2

# --- model verdict box ---------------------------------------------------
MODEL_LINES = [
    Line("Model verdict", BODY, True),
    Line("decision / guard / noise", SEC, fill=SEC_FILL),
    Line("temperature zero", SEC, fill=SEC_FILL),
    Line("cached by content", SEC, fill=SEC_FILL),
]
MODEL_H = box_h_for(len(MODEL_LINES))
MODEL_W = box_width_for([(ln.text, ln.size, ln.bold) for ln in MODEL_LINES], pad=PAD)
MODEL_X = PANEL_X + PANEL_W + CORRIDOR
MODEL_Y = Y_MID - MODEL_H / 2

# --- outcome boxes ---------------------------------------------------------
OUTCOMES = [("Decision node", "green"), ("Guarded step", "white"), ("Discarded", "grey")]
OUT_H = BOX_H
OUT_GAP = CHAIN_GAP
OUT_W = box_width_for([(t, BODY, False) for t, _ in OUTCOMES], pad=PAD)
BUS_STUB = 24
BRANCH = 50
MODEL_R = MODEL_X + MODEL_W
BUS_X = MODEL_R + BUS_STUB
OUT_X = BUS_X + BRANCH
pitch = OUT_H + OUT_GAP
out_span = (len(OUTCOMES) - 1) * pitch + OUT_H
out_top = Y_MID - out_span / 2
out_y = [out_top + i * pitch for i in range(len(OUTCOMES))]
out_mid = [y + OUT_H / 2 for y in out_y]
out_bottom = out_y[-1] + OUT_H

# --- caption ---------------------------------------------------------
W = OUT_X + OUT_W + M
CAPTION = ("The deterministic stage ranks. The model stage decides which "
           "candidates survive to the page.")
DET_LABEL_Y = PANEL_Y + PANEL_H + 22
lowest = max(chain_bottom, DET_LABEL_Y + 4, MODEL_Y + MODEL_H, out_bottom)
caption_top = lowest + 40
cap_lines = wrap(CAPTION, W - 2 * M, SEC)
H = caption_top + (len(cap_lines) - 1) * 16 + 20 + M

s = Svg(W, H)

# left chain
for i, (label, color, sub) in enumerate(CHAIN_LABELS):
    lines = [Line(label)]
    if sub:
        lines.append(Line(sub, SEC, fill=SEC_FILL))
    s.labelled_box(CHAIN_X, chain_y[i], CHAIN_W, BOX_H, lines, color)
    if i:
        s.path([(chain_cx, chain_y[i - 1] + BOX_H), (chain_cx, chain_y[i])])

# chain -> panel: out of the last box, up the corridor lane, into the panel
last_mid = chain_y[-1] + BOX_H / 2
s.path([(CHAIN_X + CHAIN_W, last_mid), (LANE_X, last_mid), (LANE_X, Y_MID), (PANEL_X, Y_MID)])

# middle panel (manual: heading + bulleted lines)
s.rect(PANEL_X, PANEL_Y, PANEL_W, PANEL_H, "blue")
head_lines = [Line(PANEL_HEAD, BODY, True)] + [Line(BULLET + b, BODY, False) for b in BULLETS]
text_block(s, PANEL_X + PAD, PANEL_Y + PAD, head_lines)
s.text(panel_cx, DET_LABEL_Y, "deterministic", SEC, fill=SEC_FILL)

# panel -> model verdict
s.path([(PANEL_X + PANEL_W, Y_MID), (MODEL_X, Y_MID)])

# model verdict box
s.labelled_box(MODEL_X, MODEL_Y, MODEL_W, MODEL_H, MODEL_LINES, "amber")

# model verdict -> bus -> outcomes
s.path([(MODEL_R, Y_MID), (BUS_X, Y_MID)], arrow=False)
s.path([(BUS_X, out_mid[0]), (BUS_X, out_mid[-1])], arrow=False)
for i, (label, color) in enumerate(OUTCOMES):
    s.path([(BUS_X, out_mid[i]), (OUT_X, out_mid[i])])
    s.labelled_box(OUT_X, out_y[i], OUT_W, OUT_H, [Line(label)], color)

# caption
for i, ln in enumerate(cap_lines):
    s.text(W / 2, caption_top + i * 16, ln, SEC, fill=SEC_FILL)

assert measure(PANEL_HEAD, BODY, True) <= PANEL_W - 2 * PAD
assert max(measure(BULLET + b, BODY) for b in BULLETS) <= PANEL_W - 2 * PAD
s.save("fig4_significance_filter.svg")
print(f"fig4 {W:.0f}x{H:.0f}  chain_w={CHAIN_W:.0f} panel={PANEL_W:.0f}x{PANEL_H:.0f} "
      f"model={MODEL_W:.0f}x{MODEL_H:.0f} out_w={OUT_W:.0f} caption_lines={len(cap_lines)}")
