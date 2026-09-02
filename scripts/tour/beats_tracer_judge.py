from tour import tour_code_snippets
from tour.tour_beat import Arm, Beat
from tour.tour_builders import ref

LANE = "tracer"
BASE = "agents/tracer_agent/tracer/services/analysis"
_VERDICT = "agents/tracer_agent/tracer/models/verdicts.py"


def beats() -> list[Beat]:
    return [
        Beat(
            "tr:judge", "step", LANE, "5 - Judge significance",
            "Stage 5 - the only place an LLM is allowed",
            "Structure is already fixed. The model's entire job is to decide which of those "
            "forks a human would actually reason about, and to write the question each asks.",
            one_liner="Which forks are decisions a human would care about?",
            detail="Three decisions in a row follow: which judge runs, whether the answer is "
                   "already cached, and what the verdict is.",
            refs=(ref(f"{BASE}/significance/significance_filter.py", 43),),
            backing=("SignificanceFilter.run",),
            facts=(("model", "haiku-4-5"), ("temperature", "0"), ("batch", "~20 forks")),
            arms=(
                Arm("tr:judge:snippet", "LlmDecisionJudge.judge", "code",
                    "Batches representatives, then fans the verdict back out to every "
                    "duplicate fork sharing that fingerprint.", kind="outcome", terminal=True,
                    refs=(ref(f"{BASE}/significance/llm_decision_judge.py", 44, 54),),
                    code=tour_code_snippets.JUDGE_CODE, code_lang="python"),
            ),
        ),
        Beat(
            "tr:judge:key", "decision", LANE, "Is an API key present?",
            "Decision - LLM or heuristic?",
            "With no API key the system does not fail - it degrades to a deterministic reach "
            "heuristic. Both arms rejoin the line, so the pipeline always completes.",
            one_liner="No key means a deterministic offline judge.",
            detail="This is why the whole pipeline can be run and tested with --no-llm, and why "
                   "a missing key is a downgrade rather than an outage.",
            refs=(ref(f"{BASE}/significance/factory.py", 51),),
            arms=(
                Arm("tr:judge:llm", "LlmDecisionJudge", "key set",
                    "Batches ~20 forks per call at temperature 0.", terminal=False,
                    refs=(ref(f"{BASE}/significance/llm_decision_judge.py", 30),)),
                Arm("tr:judge:heur", "HeuristicDecisionJudge", "no key",
                    "Pure reach heuristic, fully offline.", terminal=False,
                    refs=(ref(f"{BASE}/significance/heuristic_decision_judge.py", 10),)),
            ),
        ),
        Beat(
            "tr:judge:cache", "decision", LANE, "Has this fork been judged before?",
            "Decision - is the verdict already cached?",
            "Verdicts are content-addressed on the fork's source, its arm labels and its reach "
            "sizes. This one branch is the difference between four minutes and three seconds.",
            one_liner="Content-addressed verdict cache.",
            detail="The fingerprint includes a PROMPT_VERSION. Change the prompt without "
                   "bumping it and stale verdicts are silently served - so the cache is only "
                   "safe because that version is part of the key.",
            refs=(ref(f"{BASE}/labelling/verdict_cache.py", 12),),
            arms=(
                Arm("tr:judge:hit", "Cache hit", "cached", "Warm run, no API call.",
                    terminal=False, refs=(ref(f"{BASE}/labelling/verdict_cache.py", 12),)),
                Arm("tr:judge:miss", "Ask the model", "cold", "Temperature 0, so repeatable.",
                    terminal=False, refs=(ref(f"{BASE}/significance/llm_decision_judge.py", 30),)),
            ),
        ),
        Beat(
            "tr:judge:verdict", "decision", LANE, "Decision, guard, or noise?",
            "Decision - decision, guard, or noise?",
            "The verdict that matters. A decision becomes a diamond with a human question on "
            "it. Noise takes the branch that stops - demoted to a deeper level, never deleted.",
            one_liner="The verdict that decides what reaches the diagram.",
            detail="Labels like 'User can access ticket?' come from this stage. Nothing is ever "
                   "deleted to make the page fit; it is only ever pushed further down.",
            refs=(ref(_VERDICT, 7),),
            arms=(
                Arm("tr:judge:real", "decision", "decision",
                    "A diamond, labelled with a question.", terminal=False,
                    refs=(ref(_VERDICT, 7),)),
                Arm("tr:judge:guard", "guarded_step", "guard",
                    "Real, but not a choice - a validation gate.", terminal=False,
                    refs=(ref(_VERDICT, 7),)),
                Arm("tr:judge:noise", "noise", "noise",
                    "Demoted to a deeper level, never deleted.", terminal=True,
                    refs=(ref(_VERDICT, 7),)),
            ),
        ),
    ]
