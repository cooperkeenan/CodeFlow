from svgkit import BODY, RADIUS, SEC, STROKE_W, DASH, Line, Svg, measure, wrap

M = 30
SEC_FILL = "#4d4d4d"
HEAD_Y = 44
CONTENT_TOP = HEAD_Y + 30

# ---------------------------------------------------------------- column 1
CODE_LINES = [
    "def view(request, ticket):",
    "    if user_can_edit(request.user):",
    "        return edit_form(ticket)",
    "    else:",
    "        return deny(request)",
]
CODE_SIZE = 12
CODE_LH = 20
GROUP_GAP_EXTRA = 16
SRC_PAD_X = 18
SRC_TOP_PAD = 24
SRC_BOTTOM_PAD = 16

SRC_X = M
code_w = max(measure(t, CODE_SIZE, mono=True) for t in CODE_LINES)
SRC_W = code_w + 2 * SRC_PAD_X
CODE_X = SRC_X + SRC_PAD_X
SRC_Y = CONTENT_TOP

baselines = []
b = SRC_Y + SRC_TOP_PAD
for i in range(len(CODE_LINES)):
    if i == 3:
        b += GROUP_GAP_EXTRA
    baselines.append(b)
    b += CODE_LH
SRC_H = baselines[-1] + SRC_BOTTOM_PAD - SRC_Y

# highlight rectangles: (if / return edit_form) and (else / return deny)
HL_PAD_X = 10
HL_TOP_MARGIN = 14
HL_BOTTOM_MARGIN = 7


def hl_rect(idx_a: int, idx_b: int) -> tuple[float, float, float, float]:
    w = max(measure(CODE_LINES[i], CODE_SIZE, mono=True) for i in (idx_a, idx_b))
    x = CODE_X - HL_PAD_X
    y = baselines[idx_a] - HL_TOP_MARGIN
    h = (baselines[idx_b] + HL_BOTTOM_MARGIN) - y
    return x, y, w + 2 * HL_PAD_X, h


green_rect = hl_rect(1, 2)
amber_rect = hl_rect(3, 4)

# ---------------------------------------------------------------- column 2
CONV_BOX_W = 100
BOX_H = 50
CHILD_GAP = 40
CHILD_DROP = 64

CONV_X = SRC_X + SRC_W + 60
CONV_W = 2 * CONV_BOX_W + CHILD_GAP
CONV_Y = CONTENT_TOP

view_x = CONV_X + (CONV_W - CONV_BOX_W) / 2
view_y = CONV_Y
child_y = view_y + BOX_H + CHILD_DROP
edit_x = CONV_X
deny_x = CONV_X + CONV_BOX_W + CHILD_GAP
mid_y = view_y + BOX_H + CHILD_DROP / 2

conv_bottom = child_y + BOX_H

# ---------------------------------------------------------------- column 3
REC_PAD_X = 16
REC_H = 96
REC_GAP = 28

rec1_lines = ["caller: view", "target: edit_form", "enclosing: branch, arm 1"]
rec2_lines = ["caller: view", "target: deny", "enclosing: branch, arm 2"]
rec_w = max(measure(t, BODY) for t in rec1_lines + rec2_lines)
REC_W = rec_w + 2 * REC_PAD_X

REC_X = CONV_X + CONV_W + 60
rec1_y = CONTENT_TOP
rec2_y = rec1_y + REC_H + REC_GAP
rec_bottom = rec2_y + REC_H

# ---------------------------------------------------------------- captions
CAPTION_GAP = 30
caption_top = max(SRC_H + SRC_Y, conv_bottom, rec_bottom) + CAPTION_GAP

CAPTION_SLACK = 14
conv_caption = wrap(
    "Two edges. The branch arm each call sits under is discarded.", CONV_W - CAPTION_SLACK, SEC
)
rec_caption = wrap(
    "The same two edges, each carrying the arm it was reached through.",
    REC_W - CAPTION_SLACK, SEC,
)
n_caption_lines = max(len(conv_caption), len(rec_caption))

W = REC_X + REC_W + M
H = caption_top + (n_caption_lines - 1) * 18 + 12 + M

s = Svg(W, H)

# ---- column 1: Source
s.text(SRC_X, HEAD_Y, "Source", BODY, bold=True, anchor="start")
s.rect(SRC_X, SRC_Y, SRC_W, SRC_H, "grey")
for i, txt in enumerate(CODE_LINES):
    s.text(CODE_X, baselines[i], txt, CODE_SIZE, anchor="start", mono=True)

def outline_rect(x: float, y: float, w: float, h: float, stroke: str) -> None:
    s.add(
        f'<rect class="frame" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
        f'rx="{RADIUS}" ry="{RADIUS}" fill="none" stroke="{stroke}" '
        f'stroke-width="{STROKE_W}" stroke-dasharray="{DASH}"/>'
    )


gx, gy, gw, gh = green_rect
outline_rect(gx, gy, gw, gh, "#82b366")
ax, ay, aw, ah = amber_rect
outline_rect(ax, ay, aw, ah, "#d79b00")

# ---- column 2: Conventional call graph
s.text(CONV_X, HEAD_Y, "Conventional call graph", BODY, bold=True, anchor="start")
s.labelled_box(view_x, view_y, CONV_BOX_W, BOX_H, [Line("view")])
s.labelled_box(edit_x, child_y, CONV_BOX_W, BOX_H, [Line("edit_form")])
s.labelled_box(deny_x, child_y, CONV_BOX_W, BOX_H, [Line("deny")])

view_cx = view_x + CONV_BOX_W / 2
for child_x in (edit_x, deny_x):
    child_cx = child_x + CONV_BOX_W / 2
    s.path([
        (view_cx, view_y + BOX_H),
        (view_cx, mid_y),
        (child_cx, mid_y),
        (child_cx, child_y),
    ])

for i, ln in enumerate(conv_caption):
    s.text(CONV_X + CONV_W / 2, caption_top + i * 18, ln, SEC, fill=SEC_FILL)

# ---- column 3: CodeFlow call sites
s.text(REC_X, HEAD_Y, "CodeFlow call sites", BODY, bold=True, anchor="start")
s.rect(REC_X, rec1_y, REC_W, REC_H, "green")
s.rect(REC_X, rec2_y, REC_W, REC_H, "amber")
REC_LH = 18


def stack_left(x: float, cy: float, lines: list[str]) -> None:
    block = (len(lines) - 1) * REC_LH
    first = cy - block / 2
    for i, t in enumerate(lines):
        s.text(x, first + i * REC_LH + 0.36 * BODY, t, BODY, anchor="start")


stack_left(REC_X + REC_PAD_X, rec1_y + REC_H / 2, rec1_lines)
stack_left(REC_X + REC_PAD_X, rec2_y + REC_H / 2, rec2_lines)

CAP_LH = 18
for i, ln in enumerate(rec_caption):
    s.text(REC_X + REC_W / 2, caption_top + i * CAP_LH, ln, SEC, fill=SEC_FILL)

s.save("fig3_call_site_context.svg")
print(f"fig3 {W:.0f}x{H:.0f}  SRC_W={SRC_W:.0f} SRC_H={SRC_H:.0f} REC_W={REC_W:.0f}")
