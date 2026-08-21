from tour.tour_beat import Arm, Beat
from tour.tour_builders import ref

LANE = "gateway"
_CFG = "api/core/config.py"


def beats() -> list[Beat]:
    return [
        Beat(
            "gw:entry", "entry", LANE, "POST /analyse",
            "CodeFlow, mapping itself",
            "This diagram is CodeFlow's own pipeline, drawn by the renderer it describes. "
            "Follow the line down the middle - that is one request being turned into a map.",
            one_liner="A user asks CodeFlow to map a repository.",
            detail="The gateway owns no analysis logic. It authenticates the request, then "
                   "orchestrates four other FastAPI services and persists what comes back.",
            refs=(ref("api/routers/analysis.py", 25),), backing=("analyse",),
            facts=(("services", "5"), ("cold run", "~4 min"), ("warm run", "~3 s")),
        ),
        Beat(
            "gw:cached", "decision", LANE, "Repo already mapped?",
            "Decision - is this repo already mapped?",
            "The first real branch. One arm ends the story immediately; the other commits to "
            "four minutes of analysis. Notice the branch that stops, and the one that rejoins.",
            one_liner="Neon is checked for a stored map before anything is re-analysed.",
            detail="Maps are keyed on (user_id, repo) and upserted, so re-running a repo "
                   "replaces its map rather than accumulating rows.",
            refs=(ref("api/services/repo_map_service.py", 26),), backing=("RepoMapService.get",),
            arms=(
                Arm("gw:cached:hit", "Serve the stored map", "already mapped",
                    "Returns in about three seconds.", terminal=True,
                    refs=(ref("api/routers/repo_maps.py", 19),)),
                Arm("gw:cached:miss", "Run the full pipeline", "cold",
                    "Every stage below has to run.", terminal=False,
                    refs=(ref("api/services/analysis_service.py", 1),)),
            ),
        ),
        Beat(
            "gw:dispatch", "step", LANE, "Fan out to the agents",
            "Five services, one orchestrator",
            "The gateway hands the repo to the profiler, tracer, layout and render agents, "
            "one HTTP hop each, and stitches their JSON back together.",
            one_liner="Profiler, tracer, layout and render - one HTTP hop each.",
            detail="Gateway to tracer and layout timeouts are 900s, because a cold trace of a "
                   "large repo genuinely takes minutes.",
            refs=(ref(_CFG, 39),),
            facts=(("timeout", "900 s"), ("tracer port", "8003")),
        ),
        Beat(
            "gw:env", "decision", LANE, "ENVIRONMENT = local?",
            "Decision - localhost or Railway?",
            "One environment variable decides whether the same code talks to four processes on "
            "this laptop or to four containers on Railway. Both arms rejoin the main line.",
            one_liner="The same code targets localhost or Railway.",
            detail="`.env` is not hot-reloaded, so the gateway has to be restarted after "
                   "changing it - a small thing that has cost real debugging time.",
            refs=(ref(_CFG, 40),),
            arms=(
                Arm("gw:env:local", "localhost:8002-8006", "local",
                    "Four uvicorn processes.", terminal=False, refs=(ref(_CFG, 10),)),
                Arm("gw:env:prod", "Railway service URLs", "production",
                    "Four deployed containers.", terminal=False, refs=(ref(_CFG, 21),)),
            ),
        ),
    ]
