from tour.tour_beat import Arm, Beat
from tour.tour_builders import ref

RENDER = "render"
FRONTEND = "frontend"
_PLACE = "agents/render_agent/placement"


def beats() -> list[Beat]:
    return [
        Beat(
            "rd:place", "step", RENDER, "Place the geometry",
            "Geometry is a server concern",
            "Every x and y on this page was computed in Python and shipped as JSON. The browser "
            "is a thin renderer - no dagre, no Mermaid, no layout in the client.",
            one_liner="Deterministic React Flow geometry.",
            detail="That is what makes the picture reproducible: the same repo in gives a "
                   "byte-identical graph out, so a diff between two runs is meaningful.",
            refs=(ref(f"{_PLACE}/flow_page_placer.py", 28),), backing=("FlowPagePlacer.place",),
            packets=("tr:budget:flow->act:delivery", "tr:budget:list->act:delivery"),
            facts=(("layout", "server-side"), ("output", "byte-identical")),
        ),
        Beat(
            "rd:spine", "decision", RENDER, "Is this node on the spine?",
            "Decision - spine, or branch?",
            "The spine is the longest reachable path through a lane, and it gets the straight "
            "line. Everything else is offset into a column beside it - exactly like this page.",
            one_liner="The longest path gets the straight line.",
            detail="The layout you are looking at right now is the same idea applied by hand: "
                   "a main line down the middle, branches to either side, converging back.",
            refs=(ref(f"{_PLACE}/spine_router.py", 25),),
            arms=(
                Arm("rd:spine:main", "Straight down the lane", "spine",
                    "Drawn as the primary path.", terminal=False,
                    refs=(ref(f"{_PLACE}/tree_layout.py", 33),)),
                Arm("rd:spine:branch", "Offset into a column", "branch",
                    "Siblings spaced so nothing overlaps.", terminal=False,
                    refs=(ref(f"{_PLACE}/tree_layout.py", 33),)),
            ),
        ),
        Beat(
            "fe:page", "step", FRONTEND, "The diagram you are looking at",
            "And this is the output",
            "A skeleton of at most 15 nodes, with every other decision one + away. On "
            "django-helpdesk that is 222 decisions sitting behind this same surface.",
            one_liner="15 visible nodes, everything else one + away.",
            detail="Positions come from the render agent, so the frontend only decides what is "
                   "revealed - never where anything goes.",
            refs=(ref("frontend/src/pages/FlowPage.jsx", 18),),
            packets=("rd:spine:main->fe:page", "rd:spine:branch->fe:page"),
            facts=(("django-helpdesk", "222 decisions"), ("visible at once", "15")),
        ),
        Beat(
            "fe:expand", "decision", FRONTEND, "Did the reader press + ?",
            "Which is what you have been reading",
            "Progressive disclosure is the last decision in the system, and it belongs to the "
            "reader. This tour is itself a CodeFlow diagram - click any node to open its source.",
            one_liner="A node's hidden_children is exactly what its + reveals.",
            detail="Both arms stop here, because this is where the pipeline hands over. "
                   "Everything you have seen was hand-authored as a FlowGraph and run through "
                   "the real placer - the same code path a real repo takes.",
            refs=(ref("frontend/src/hooks/useExpansion.js", 16),),
            arms=(
                Arm("fe:expand:open", "Reveal the nested decisions", "expand",
                    "The camera flies to what was revealed.", terminal=True,
                    refs=(ref("frontend/src/components/flow/CameraController.jsx", 29),)),
                Arm("fe:expand:shut", "Stay at this level", "collapsed",
                    "The skeleton never grows past 15.", terminal=True,
                    refs=(ref("frontend/src/hooks/useExpansion.js", 30),)),
            ),
        ),
    ]
