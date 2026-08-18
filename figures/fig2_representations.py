from svgkit import BODY, SEC, Line, Svg, measure, wrap

M = 30
PANEL_GAP = 24
PANEL_W = 408
PAD = 16
INNER = PANEL_W - 2 * PAD
W = 2 * M + 2 * PANEL_W + PANEL_GAP

SEC_FILL = "#4d4d4d"
LABEL_Y = 44
FRAME_Y = 56

COL_W, COL_GAP = 112, 20
NODE_H = 44
FLOW_H = 52

LEFT_X = M
RIGHT_X = M + PANEL_W + PANEL_GAP


def columns(panel_x: float) -> list[float]:
    x0 = panel_x + PAD
    return [x0 + i * (COL_W + COL_GAP) + COL_W / 2 for i in range(3)]


left_cols = columns(LEFT_X)
right_cols = columns(RIGHT_X)
left_mid = LEFT_X + PANEL_W / 2
right_mid = RIGHT_X + PANEL_W / 2

ROOT_W, ENGINE_W = 172, 148
LEFT_VGAP = 62
left_rows = [FRAME_Y + PAD + i * (NODE_H + LEFT_VGAP) for i in range(4)]
left_content_h = left_rows[-1] + NODE_H - (FRAME_Y + PAD)

ENTRY_W, DIA_W, DIA_H = 200, 210, 92
EFFECT_W = 184
ARM_DROP = 16
ARM_LABEL_GAP = 34
MERGE_DROP = 20
MERGE_TO_EFFECT = 30
r_entry_y = FRAME_Y + PAD
r_dia_cy = r_entry_y + FLOW_H + 40 + DIA_H / 2
r_fan_y = r_dia_cy + DIA_H / 2 + ARM_DROP
r_out_y = r_fan_y + ARM_LABEL_GAP
r_merge_y = r_out_y + FLOW_H + MERGE_DROP
r_eff_y = r_merge_y + MERGE_TO_EFFECT
right_content_h = r_eff_y + FLOW_H - (FRAME_Y + PAD)

CAP_LINES = 2
content_h = max(left_content_h, right_content_h)
cap_top = FRAME_Y + PAD + content_h + 26
PANEL_H = cap_top + CAP_LINES * 16 + PAD - FRAME_Y
H = FRAME_Y + PANEL_H + M + 2

s = Svg(W, H)

for x, title in ((LEFT_X, "Structural representation"), (RIGHT_X, "Decision representation")):
    s.text(x, LABEL_Y, title, BODY, bold=True, anchor="start")
    s.rect(x, FRAME_Y, PANEL_W, PANEL_H, "panel", cls="frame", radius=4)

art = "grey"
s.labelled_box(left_mid - ROOT_W / 2, left_rows[0], ROOT_W, NODE_H,
               [Line("ScrapingOrchestrator")], art)
s.labelled_box(left_mid - ENGINE_W / 2, left_rows[1], ENGINE_W, NODE_H,
               [Line("MatchingEngine")], art)
for i, name in enumerate(["TitleMatcher", "PriceMatcher", "KeywordFilter"]):
    s.labelled_box(left_cols[i] - COL_W / 2, left_rows[2], COL_W, NODE_H, [Line(name)], art)
for i, name in enumerate(["Product", "Listing", "MatchResult"]):
    s.labelled_box(left_cols[i] - COL_W / 2, left_rows[3], COL_W, NODE_H, [Line(name)], art)

s.path([(left_mid, left_rows[0] + NODE_H), (left_mid, left_rows[1])])
fan_y = left_rows[1] + NODE_H + LEFT_VGAP / 2
s.path([(left_mid, left_rows[1] + NODE_H), (left_mid, fan_y)], arrow=False)
s.path([(left_cols[0], fan_y), (left_cols[2], fan_y)], arrow=False)
for cx in left_cols:
    s.path([(cx, fan_y), (cx, left_rows[2])])
    s.path([(cx, left_rows[2] + NODE_H), (cx, left_rows[3])])

flow, effect = "green", "amber"
s.labelled_box(right_mid - ENTRY_W / 2, r_entry_y, ENTRY_W, FLOW_H,
               [Line("scrape_and_match()"), Line("entry point", SEC, fill=SEC_FILL)], flow)
s.path([(right_mid, r_entry_y + FLOW_H), (right_mid, r_dia_cy - DIA_H / 2)])

s.polygon([(right_mid, r_dia_cy - DIA_H / 2), (right_mid + DIA_W / 2, r_dia_cy),
           (right_mid, r_dia_cy + DIA_H / 2), (right_mid - DIA_W / 2, r_dia_cy)], flow)
q_lines = ["Which matching", "strategy?"]
s.stack_text(right_mid, r_dia_cy, [Line(t) for t in q_lines])

s.path([(right_mid, r_dia_cy + DIA_H / 2), (right_mid, r_fan_y)], arrow=False)
s.path([(right_cols[0], r_fan_y), (right_cols[2], r_fan_y)], arrow=False)
outcomes = [("Exact title", "match"), ("Price-band", "match"), ("Keyword", "fallback")]
arms = ["title", "price", "keyword"]
ARM_LABEL_DX = 16
arm_label_y = r_fan_y + ARM_LABEL_GAP / 2 + 0.36 * SEC
for i, cx in enumerate(right_cols):
    s.path([(cx, r_fan_y), (cx, r_out_y)])
    s.text(cx + ARM_LABEL_DX, arm_label_y, arms[i], SEC, anchor="start", fill=SEC_FILL)
    s.labelled_box(cx - COL_W / 2, r_out_y, COL_W, FLOW_H,
                   [Line(t) for t in outcomes[i]], flow)

for cx in right_cols:
    s.path([(cx, r_out_y + FLOW_H), (cx, r_merge_y)], arrow=False)
s.path([(right_cols[0], r_merge_y), (right_cols[2], r_merge_y)], arrow=False)
s.path([(right_mid, r_merge_y), (right_mid, r_eff_y)])
s.labelled_box(right_mid - EFFECT_W / 2, r_eff_y, EFFECT_W, FLOW_H,
               [Line("write match_results"), Line("effect", SEC, fill=SEC_FILL)], effect)

left_cap = wrap("Twenty components. Which strategy runs, and on what basis, "
                "is not represented.", INNER, SEC)
right_cap = wrap("Entry points, decisions, effects and outcomes.", INNER, SEC)
for i, ln in enumerate(left_cap):
    s.text(left_mid, cap_top + i * 16, ln, SEC, fill=SEC_FILL)
for i, ln in enumerate(right_cap):
    s.text(right_mid, cap_top + i * 16, ln, SEC, fill=SEC_FILL)

for i, ln in enumerate(q_lines):
    dy = abs((len(q_lines) - 1) / 2 - i) * 16 + 8
    half = (DIA_W / 2) * (1 - 2 * dy / DIA_H)
    assert measure(ln, BODY) < 2 * half - 8, f"{ln!r} does not fit the diamond"
assert len(left_cap) <= CAP_LINES and len(right_cap) <= CAP_LINES
s.save("fig2_representations.svg")
print(f"fig2 {W:.0f}x{H:.0f}  left_content={left_content_h:.0f} right_content={right_content_h:.0f}")
