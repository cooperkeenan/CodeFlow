from tour import tour_code_snippets
from tour.tour_beat import Arm, Beat
from tour.tour_builders import ref

LANE = "tracer"
BASE = "agents/tracer_agent/services/analysis"
MODELS = "agents/tracer_agent/models"

_FORKS = [
    ("branch", "if / elif / else"), ("match", "match statement"),
    ("except", "try / except handler"), ("route", "HTTP route table"),
    ("table", "dict or registry lookup"), ("polymorphic", "subclass override"),
    ("dynamic", "getattr / runtime name"),
]

_EFFECTS = [
    ("http_out", "Outbound HTTP", "httpx / requests"), ("database", "Database", "session.query"),
    ("llm", "LLM", "messages.create"), ("file", "Filesystem", "Path.read_text"),
    ("queue", "Queue", "publish / enqueue"), ("email", "Email", "send_mail"),
    ("response", "Response", "returns to caller"),
]


def _fork_arms() -> tuple[Arm, ...]:
    return tuple(
        Arm(f"tr:fork:{kind}", kind, kind, desc, terminal=False,
            refs=(ref(f"{BASE}/dispatch_extractor.py", 12),))
        for kind, desc in _FORKS
    )


def _effect_arms() -> tuple[Arm, ...]:
    return tuple(
        Arm(f"tr:eff:{kind}", label, kind, hint, kind="effect", terminal=True,
            refs=(ref(f"{BASE}/effect_detector.py", 25),),
            effect_kind=kind, effect_target=hint)
        for kind, label, hint in _EFFECTS
    )


def beats() -> list[Beat]:
    return [
        Beat(
            "tr:index", "step", LANE, "1 - Index the repo",
            "Stage 1 - index every symbol",
            "Every function in the repo becomes a symbol, and every import is resolved to a "
            "real file. This is the foundation the whole call graph stands on.",
            one_liner="Function-level symbol table for the whole repo.",
            detail="Source roots are derived from where imports actually bind, never from "
                   "directory names. Assuming a folder was called 'agents' once resolved almost "
                   "every internal call to 'ext:' and shredded the entire call graph.",
            refs=(ref(f"{BASE}/project_indexer.py", 25),), backing=("ProjectIndexer.index",),
            packets=("gw:env:local->act:static", "gw:env:prod->act:static"),
            arms=(
                Arm("tr:index:snippet", "ProjectIndexer.index", "code",
                    "One file at a time: parse, then bucket classes and functions.",
                    kind="outcome", terminal=True,
                    refs=(ref(f"{BASE}/project_indexer.py", 32, 40),),
                    code=tour_code_snippets.INDEX_CODE, code_lang="python"),
            ),
        ),
        Beat(
            "tr:import", "decision", LANE, "Where does this import resolve?",
            "Decision - project, stdlib, or third party?",
            "Ancestor prefixes are walked longest-first, so any directory layout works. Only "
            "the project arm rejoins the line; the other two genuinely stop here.",
            one_liner="Longest-prefix ancestor walk, stdlib short-circuited.",
            detail="This exact function has been the site of two outages. Both were the same "
                   "bug: hardcoding this repo's own folder names into the resolver.",
            refs=(ref(f"{BASE}/path_fqn.py", 29),),
            arms=(
                Arm("tr:import:internal", "Project module", "project",
                    "Becomes a call-graph edge.", terminal=False,
                    refs=(ref(f"{BASE}/path_fqn.py", 24),)),
                Arm("tr:import:stdlib", "Standard library", "stdlib",
                    "Short-circuits the walk.", terminal=True,
                    refs=(ref(f"{BASE}/path_fqn.py", 4),)),
                Arm("tr:import:ext", "Third party -> ext:", "third party",
                    "Not traced any further.", terminal=True,
                    refs=(ref(f"{BASE}/path_fqn.py", 33),)),
            ),
        ),
        Beat(
            "tr:resolve", "step", LANE, "2 - Resolve the call graph",
            "Stage 2 - resolve the call graph",
            "Each call site is bound to a target, carrying the control context it sits inside - "
            "which if, which except, which loop.",
            one_liner="Call graph with per-call-site control context.",
            detail="The control context is what later lets a fork be described as a decision "
                   "rather than just a branch instruction.",
            refs=(ref(f"{BASE}/call_resolver.py", 41),), backing=("CallResolver.resolve_project",),
            arms=(
                Arm("tr:resolve:snippet", "CallResolver.resolve_project", "code",
                    "Control context - scope, local bindings, self types - travels with "
                    "the call site.", kind="outcome", terminal=True,
                    refs=(ref(f"{BASE}/call_resolver.py", 49, 56),),
                    code=tour_code_snippets.RESOLVE_CODE, code_lang="python"),
            ),
        ),
        Beat(
            "tr:target", "decision", LANE, "Can the target be resolved statically?",
            "Decision - resolved or inferred?",
            "Confidence is recorded, never guessed away. An inferred edge is drawn faded on the "
            "final diagram rather than being quietly promoted to a fact.",
            one_liner="Confidence is carried through to the picture.",
            detail="Both arms rejoin the line - an uncertain edge is still an edge.",
            refs=(ref(f"{MODELS}/resolved_target.py", 8),),
            arms=(
                Arm("tr:target:resolved", "resolved", "static", "Exact function known.",
                    terminal=False, refs=(ref(f"{MODELS}/resolved_target.py", 8),)),
                Arm("tr:target:inferred", "inferred", "ambiguous", "Drawn faded.",
                    terminal=False, refs=(ref(f"{MODELS}/resolved_target.py", 8),)),
            ),
        ),
        Beat(
            "tr:forks", "decision", LANE, "3 - What kind of fork is this?",
            "Stage 3 - extract every fork",
            "The heart of it. Static analysis finds every branch point in the repo and sorts it "
            "into one of seven shapes. Watch all seven arms converge back into the main line.",
            one_liner="Seven kinds of branch point, no exceptions.",
            detail="Static analysis owns structure. The LLM that runs two stages later may "
                   "judge these forks and label them, but it may never add, remove, merge or "
                   "rewire a single one.",
            refs=(ref(f"{MODELS}/dispatch_site.py", 7),), backing=("DispatchExtractor.extract",),
            arms=_fork_arms(),
            facts=(("fork kinds", "7"), ("on django-helpdesk", "222 decisions")),
        ),
        Beat(
            "tr:effects", "step", LANE, "4 - Detect side effects",
            "Stage 4 - what touches the outside world?",
            "Seven effect kinds hang off the line as annotations. These become the icons on the "
            "diagram, and they are what makes cross-service stitching possible later.",
            one_liner="http, db, llm, file, queue, email, response.",
            detail="Effects are annotations, not control flow, so these branches stop rather "
                   "than rejoining. A call made inside a third-party SDK produces no effect - "
                   "a known and deliberate blind spot.",
            refs=(ref(f"{BASE}/effect_detector.py", 25),), backing=("EffectDetector.detect",),
            arms=_effect_arms(),
        ),
    ]
