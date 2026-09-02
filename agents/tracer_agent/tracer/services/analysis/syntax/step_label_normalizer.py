import re

_RECEIVER_RE = re.compile(r"^(self\.|super\(\)\.)")
_CALL_KINDS = frozenset({"call", "effect"})
_SELF_STRIP_KINDS = frozenset({"decision", "return", "raise", "loop"})
_GETTEXT_NAMES = frozenset({"_", "gettext", "ugettext", "gettext_lazy", "ugettext_lazy"})
_GENERIC_NAMES = frozenset({"getattr", "setattr", "hasattr"})
_LITERAL_RE = re.compile(r"""['"]([^'"]{1,40})""")


def _drop_args(text: str) -> str:
    index = text.find("(")
    return text if index == -1 else text[:index]


def _first_literal(text: str) -> str:
    index = text.find("(")
    if index == -1:
        return ""
    match = _LITERAL_RE.search(text[index:])
    return match.group(1).strip() if match else ""


def _humanise(segment: str) -> str:
    stripped = segment.lstrip("_")
    if not stripped:
        return segment
    return stripped.replace("_", " ")


def _display_call_label(text: str) -> str:
    bare = _RECEIVER_RE.sub("", text)
    callee = _drop_args(bare)
    last = callee.rsplit(".", 1)[-1]
    if last in _GETTEXT_NAMES:
        literal = _first_literal(text)
        return f'"{literal}"' if literal else callee
    if last in _GENERIC_NAMES:
        literal = _first_literal(text)
        return f"{last} {literal}" if literal else callee
    return callee if "." in callee else _humanise(callee)


def _strip_self(text: str) -> str:
    return text.replace("self.", "")


def normalize_label(kind: str, raw: str) -> str:
    text = raw or ""
    if kind in _CALL_KINDS:
        return _display_call_label(text)
    if kind in _SELF_STRIP_KINDS:
        return _strip_self(text)
    return text
