import re

from shared.models.flow_graph import EffectKind

_EFFECT_NOUNS: dict[str, str] = {
    "http_out": "Call",
    "database": "Store",
    "llm": "Ask LLM",
    "file": "File",
    "queue": "Enqueue",
    "email": "Email",
    "response": "Respond",
}

_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


class LabelSynthesizer:
    def humanize(self, fqn: str) -> str:
        tail = fqn.split(".")[-1]
        if tail == "<module>":
            tail = fqn.split(".")[-2] if "." in fqn else tail
        tail = tail.removeprefix("_")
        spaced = _CAMEL.sub(" ", tail).replace("_", " ").strip()
        words = [w for w in spaced.split(" ") if w]
        return " ".join(w[:1].upper() + w[1:] for w in words) or tail

    def step_label(self, backing: list[str]) -> str:
        project = [b for b in backing if not b.startswith("ext:")]
        chosen = project[0] if project else backing[0]
        return self.humanize(chosen)

    def effect_label(self, kind: EffectKind, target: str) -> str:
        noun = _EFFECT_NOUNS.get(kind, kind.title())
        if target and kind in {"database", "http_out", "llm"}:
            return f"{noun}: {self.humanize(target)}"
        return noun

    def decision_label(self, selector_source: str) -> str:
        text = selector_source.strip()
        return text[:60] if text else "Decision"
