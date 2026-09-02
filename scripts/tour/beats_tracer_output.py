from tour.tour_beat import Arm, Beat
from tour.tour_builders import ref

LANE = "tracer"
BASE = "agents/tracer_agent/tracer/services/analysis"


def beats() -> list[Beat]:
    return [
        Beat(
            "tr:condense", "step", LANE, "6 - Condense to a FlowGraph",
            "Stage 6 - condense to a graph",
            "Judged forks are projected onto the node kinds you have been looking at all along: "
            "entry, step, decision, parallel, effect and outcome.",
            one_liner="Projection onto entry/step/decision/effect/outcome.",
            detail="This is where the diagram's vocabulary is fixed. Straight-line step chains "
                   "are merged here so the picture is not padded with pass-through boxes.",
            refs=(ref(f"{BASE}/condense/flow_condenser.py", 34),), backing=("FlowCondenser.condense",),
        ),
        Beat(
            "tr:cond:arm", "decision", LANE, "Does this arm reach further code?",
            "Decision - does this arm go anywhere?",
            "An arm that stops has to be given an honest ending rather than trailing off the "
            "page. Fittingly, one of these two branches stops and the other carries on.",
            one_liner="Arms that terminate get a named outcome.",
            detail="OutcomeLabeler names the dead end Returns, Raises or Continues - or uses a "
                   "label the judge supplied.",
            refs=(ref(f"{BASE}/condense/flow_condenser.py", 34),),
            arms=(
                Arm("tr:cond:more", "Continue the flow", "reaches code",
                    "Points at the next real node.", terminal=False,
                    refs=(ref(f"{BASE}/condense/flow_condenser.py", 34),)),
                Arm("tr:cond:end", "Returns / Raises / Continues", "terminates",
                    "An honest ending, not a loose edge.", terminal=True,
                    refs=(ref("agents/tracer_agent/tracer/models/call_records.py", 28),)),
            ),
        ),
        Beat(
            "tr:stitch", "step", LANE, "7 - Stitch the services together",
            "Stage 7 - join the services up",
            "An outbound HTTP call in one service and a route in another are the same edge. "
            "This is the stage that turns four separate graphs into one system.",
            one_liner="Outbound calls matched to route entries.",
            detail="Without this, a microservice repo renders as several disconnected islands.",
            refs=(ref(f"{BASE}/stitch/flow_stitcher.py", 11),), backing=("FlowStitcher.stitch",),
        ),
        Beat(
            "tr:stitch:url", "decision", LANE, "Does the URL match a known route?",
            "Decision - matched, or judged?",
            "Deterministic URL matching goes first. Only what is left over is put to the model, "
            "and those edges are drawn faded because they are inferred, not proven.",
            one_liner="URL matching first, the model only for leftovers.",
            detail="The same discipline as everywhere else: the cheap deterministic path runs "
                   "first, and the LLM is the fallback rather than the default.",
            refs=(ref(f"{BASE}/stitch/http_stitch_detector.py", 1),),
            arms=(
                Arm("tr:stitch:http", "HttpStitchDetector", "matched",
                    "Deterministic URL match.", terminal=False,
                    refs=(ref(f"{BASE}/stitch/http_stitch_detector.py", 1),)),
                Arm("tr:stitch:llm", "LlmStitchDetector", "unresolved",
                    "Judged, and drawn as an inferred edge.", terminal=False,
                    refs=(ref(f"{BASE}/stitch/llm_stitch_detector.py", 1),)),
            ),
        ),
        Beat(
            "tr:budget", "step", LANE, "8 - Budget the page",
            "Stage 8 - fit the page without losing anything",
            "The rule that shapes every CodeFlow diagram: the first view of a codebase is at "
            "most 15 nodes. Nothing is deleted to achieve that.",
            one_liner="Nothing is deleted - detail is demoted.",
            detail="A node's hidden_children is exactly what its + reveals. A + that opens 50 "
                   "nodes at once is treated as a bug, not as disclosure.",
            refs=(ref(f"{BASE}/budget/visibility_budgeter.py", 55),),
            backing=("VisibilityBudgeter.budget",),
            facts=(("top-level budget", "15 nodes"), ("deleted", "nothing")),
        ),
        Beat(
            "tr:budget:over", "decision", LANE, "More than 15 nodes on top?",
            "Decision - demote, or keep?",
            "When the page is over budget the low-ranked nodes move behind a + on their parent. "
            "Both arms rejoin: whichever way it goes, the node still exists.",
            one_liner="Over budget means demoted, not dropped.",
            detail="This is the difference between a summary and a lie. Every node in the "
                   "original graph is still reachable from the rendered page.",
            refs=(ref(f"{BASE}/budget/visibility_budgeter.py", 55),),
            arms=(
                Arm("tr:budget:demote", "Demote, never delete", "over budget",
                    "Moves behind a + on its parent.", terminal=False,
                    refs=(ref(f"{BASE}/budget/containment_indexer.py", 1),)),
                Arm("tr:budget:keep", "Keep on the skeleton", "fits",
                    "High-ranked nodes stay visible.", terminal=False,
                    refs=(ref(f"{BASE}/budget/visibility_budgeter.py", 55),)),
            ),
        ),
        Beat(
            "tr:budget:body", "decision", LANE, "Is this body a flow or a list?",
            "Decision - flow or list?",
            "A sequence chains; a decision's arms are mutually exclusive alternatives. This is "
            "derived from the body's actual shape - it is not asserted.",
            one_liner="Derived from shape, never asserted.",
            detail="Asserting single-entry as an invariant crashed the pipeline on CodeFlow's "
                   "own repo: a shared memoized node can legitimately be both a predecessor of "
                   "a body member and a containment ancestor of it.",
            refs=(ref(f"{BASE}/budget/containment_indexer.py", 1),),
            arms=(
                Arm("tr:budget:flow", "flow - chain them", "single entry",
                    "One entry, sequential members.", terminal=False,
                    refs=(ref(f"{BASE}/budget/containment_indexer.py", 1),)),
                Arm("tr:budget:list", "list - alternatives", "alternatives",
                    "Mutually exclusive arms.", terminal=False,
                    refs=(ref(f"{BASE}/budget/containment_indexer.py", 1),)),
            ),
        ),
    ]
