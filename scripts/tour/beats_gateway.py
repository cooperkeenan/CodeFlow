from tour.tour_beat import Arm, Beat
from tour.tour_builders import ref

LANE = "gateway"
_CFG = "api/gateway/core/config.py"


def beats() -> list[Beat]:
    return [
        Beat(
            "gw:entry", "entry", LANE, "POST /ci/analyse/local",
            "CodeFlow, mapping itself",
            "This diagram is CodeFlow's own pipeline, drawn by the renderer it describes. "
            "Follow the line down the middle - that is one request being turned into a map.",
            one_liner="A user asks CodeFlow to map a repository.",
            detail="The gateway owns no analysis logic. It authenticates the request, then "
                   "orchestrates three other FastAPI services and persists what comes back.",
            refs=(ref("api/gateway/routers/ci.py", 48),), backing=("ci_analyse_local",),
            facts=(("services", "4"), ("cold run", "~4 min"), ("warm run", "~3 s")),
        ),
        Beat(
            "gw:cached", "decision", LANE, "Repo already mapped?",
            "Decision - is this repo already mapped?",
            "The first real branch. One arm ends the story immediately; the other commits to "
            "four minutes of analysis. Notice the branch that stops, and the one that rejoins.",
            one_liner="Neon is checked for a stored map before anything is re-analysed.",
            detail="Maps are keyed on (user_id, repo) and upserted, so re-running a repo "
                   "replaces its map rather than accumulating rows.",
            refs=(ref("api/gateway/services/repo_map_service.py", 25),), backing=("RepoMapService.get",),
            arms=(
                Arm("gw:cached:hit", "Serve the stored map", "already mapped",
                    "Returns in about three seconds.", terminal=True,
                    refs=(ref("api/gateway/routers/repo_maps.py", 60),)),
                Arm("gw:cached:miss", "Run the full pipeline", "cold",
                    "Every stage below has to run.", terminal=False,
                    refs=(ref("api/gateway/services/analysis_service.py", 1),)),
            ),
        ),
        Beat(
            "gw:dispatch", "step", LANE, "Fan out to the agents",
            "Four services, one orchestrator",
            "The gateway hands the repo to the profiler, tracer and render agents, "
            "one HTTP hop each, and stitches their JSON back together.",
            one_liner="Profiler, tracer and render - one HTTP hop each.",
            detail="Gateway to tracer timeout is 900s, because a cold trace of a "
                   "large repo genuinely takes minutes.",
            refs=(ref(_CFG, 26),),
            facts=(("timeout", "900 s"), ("tracer port", "8003")),
        ),
        Beat(
            "gw:env", "decision", LANE, "ENVIRONMENT = local?",
            "Decision - localhost or Railway?",
            "One environment variable decides whether the same code talks to three processes on "
            "this laptop or to three containers on Railway. Both arms rejoin the main line.",
            one_liner="The same code targets localhost or Railway.",
            detail="`.env` is not hot-reloaded, so the gateway has to be restarted after "
                   "changing it - a small thing that has cost real debugging time.",
            refs=(ref(_CFG, 43),),
            arms=(
                Arm("gw:env:local", "localhost:8002-8004", "local",
                    "Three uvicorn processes.", terminal=False, refs=(ref(_CFG, 13),)),
                Arm("gw:env:prod", "Railway service URLs", "production",
                    "Three deployed containers.", terminal=False, refs=(ref(_CFG, 24),)),
            ),
        ),
    ]
