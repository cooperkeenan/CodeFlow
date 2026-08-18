from svgkit import BODY, SEC, Line, Svg, measure, wrap

M = 30
SEC_FILL = "#4d4d4d"

LEFT_X, LEFT_W = M, 232
CORRIDOR = 140
AGENT_X, AGENT_W = LEFT_X + LEFT_W + CORRIDOR, 168
AGENT_R = AGENT_X + AGENT_W
MODEL_GAP = 90
ANTH_X, ANTH_W = AGENT_R + MODEL_GAP, 120
W = ANTH_X + ANTH_W + M

BOX_H, TALL_H = 52, 52
AGENT_PITCH = 82
AGENT_Y0 = 74

HEAD_Y = 44
BUS_X = LEFT_X + LEFT_W + 22

AGENTS = [
    ("Profiler", "POST /profile", "white", "RepoBlueprint"),
    ("Tracer", "POST /trace", "green", "FlowGraph"),
    ("Layout", "POST /layout", "white", "FlowGraph"),
    ("Render", "POST /render", "white", "RenderedView"),
    ("Explain", "POST /explain", "white", "ExplainResponse"),
]
STAGES = ["Index", "Resolve", "Extract", "Score", "Judge", "Condense", "Budget", "Render"]
AMBER_STAGE = "Judge"

agent_top = [AGENT_Y0 + i * AGENT_PITCH for i in range(len(AGENTS))]
agent_mid = [t + TALL_H / 2 for t in agent_top]
stack_bottom = agent_top[-1] + TALL_H
stack_mid = (agent_top[0] + stack_bottom) / 2

gw_y = stack_mid - TALL_H / 2
gw_bottom = gw_y + TALL_H
react_y = gw_y - 62 - BOX_H
ext_y = gw_bottom + 54
ext_w = (LEFT_W - 16) / 2

anth_mid = (agent_mid[1] + agent_mid[4]) / 2
ANTH_H = TALL_H
ENTRY_STEP = 16
anth_y = anth_mid - ANTH_H / 2

STAGE_Y = stack_bottom + 62
stage_gap = 20
stage_w = (W - 2 * M - (len(STAGES) - 1) * stage_gap) / len(STAGES)
caption_y = STAGE_Y + BOX_H + 30
H = caption_y + 12 + M

s = Svg(W, H)

s.text(LEFT_X, HEAD_Y, "Services", BODY, bold=True, anchor="start")

s.labelled_box(LEFT_X, react_y, LEFT_W, BOX_H, [Line("React frontend")])
s.path([(LEFT_X + LEFT_W / 2, react_y + BOX_H), (LEFT_X + LEFT_W / 2, gw_y)])
s.text(LEFT_X + LEFT_W / 2 + 9, (react_y + BOX_H + gw_y) / 2 + 4, "HTTP / JSON", SEC,
       anchor="start", fill=SEC_FILL)

s.labelled_box(LEFT_X, gw_y, LEFT_W, TALL_H, [Line("Gateway (FastAPI)")], "blue")

for i, name in enumerate(["Neon Postgres", "GitHub API"]):
    ex = LEFT_X + i * (ext_w + 16)
    cx = ex + ext_w / 2
    s.path([(cx, gw_bottom), (cx, ext_y)])
    s.labelled_box(ex, ext_y, ext_w, BOX_H, [Line(name)], "grey")

s.path([(LEFT_X + LEFT_W, stack_mid), (BUS_X, stack_mid)], arrow=False)
s.path([(BUS_X, agent_mid[0]), (BUS_X, agent_mid[-1])], arrow=False)

for i, (name, endpoint, color, schema) in enumerate(AGENTS):
    s.labelled_box(AGENT_X, agent_top[i], AGENT_W, TALL_H,
                   [Line(name), Line(endpoint, SEC, fill=SEC_FILL)], color)
    s.path([(BUS_X, agent_mid[i]), (AGENT_X, agent_mid[i])])
    s.text((BUS_X + AGENT_X) / 2, agent_mid[i] - 10, schema, SEC, fill=SEC_FILL)

lanes = {1: AGENT_R + 42, 2: AGENT_R + 20, 4: AGENT_R + 64}
entry = {1: anth_mid - ENTRY_STEP, 2: anth_mid, 4: anth_mid + ENTRY_STEP}
for idx in (1, 2, 4):
    lane, ey = lanes[idx], entry[idx]
    s.path([(AGENT_R, agent_mid[idx]), (lane, agent_mid[idx]), (lane, ey), (ANTH_X, ey)],
           dashed=True)

s.text(ANTH_X + ANTH_W / 2, anth_y - 12, "model calls", SEC, fill=SEC_FILL)
s.labelled_box(ANTH_X, anth_y, ANTH_W, ANTH_H, [Line("Anthropic"), Line("API")], "grey")

s.text(LEFT_X, stack_bottom + 46, "Tracer stages", BODY, bold=True, anchor="start")

for i, name in enumerate(STAGES):
    x = M + i * (stage_w + stage_gap)
    color = "amber" if name == AMBER_STAGE else "white"
    s.labelled_box(x, STAGE_Y, stage_w, BOX_H, [Line(name)], color)
    if i:
        s.path([(x - stage_gap, STAGE_Y + BOX_H / 2), (x, STAGE_Y + BOX_H / 2)])

cap = ("Stages 1 to 4 and 6 to 8 are pure functions of the source tree. "
       "Stage 5 is the only model-driven step.")
lines = wrap(cap, W - 2 * M, SEC)
for i, ln in enumerate(lines):
    s.text(W / 2, caption_y + i * 16, ln, SEC, fill=SEC_FILL)

assert measure(max(AGENTS, key=lambda a: measure(a[3], SEC))[3], SEC) < AGENT_X - BUS_X - 24
s.save("fig1_architecture.svg")
print(f"fig1 {W:.0f}x{H:.0f}, caption lines={len(lines)}")
