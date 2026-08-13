"""Canonical route form.

Exact-match set comparison is only meaningful if both sides agree on what a route
*is*. Without this, precision and recall are dominated by trailing slashes and
converter syntax rather than by anything the tool got right or wrong.

Canonical form: ``METHOD /segment/{}/segment`` — method uppercased, every path
parameter collapsed positionally to ``{}``, no trailing slash, no regex anchors.
"""

import re

_NAMED_GROUP = re.compile(r"\(\?P<[^>]*>(?:[^()\\]|\\.)*\)")
_GROUP = re.compile(r"\((?:[^()\\]|\\.)*\)")
_ANGLE = re.compile(r"<[^>]*>")
_BRACE = re.compile(r"\{[^}]*\}")
_SLASHES = re.compile(r"/{2,}")

PARAM = "{}"

CANONICAL_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE")


class RouteNormalizer:
    """Collapses framework-specific route syntax to one comparable string."""

    def canonical(self, method: str, path: str) -> str:
        return f"{self.method(method)} {self.path(path)}"

    def method(self, method: str) -> str:
        cleaned = (method or "").strip().upper()
        return cleaned if cleaned else "GET"

    def path(self, path: str) -> str:
        text = (path or "").strip()
        text = text.lstrip("^").rstrip("$")
        text = _NAMED_GROUP.sub(PARAM, text)
        text = _GROUP.sub(PARAM, text)
        text = _ANGLE.sub(PARAM, text)
        text = _BRACE.sub(PARAM, text)
        text = text.replace("\\", "")
        text = _SLASHES.sub("/", text)
        if not text.startswith("/"):
            text = "/" + text
        if len(text) > 1:
            text = text.rstrip("/")
        return text or "/"

    def expand(self, methods: tuple[str, ...], path: str) -> tuple[str, ...]:
        """One canonical string per HTTP method, sorted and de-duplicated."""
        chosen = tuple(m for m in methods if m.strip()) or ("GET",)
        canonical_path = self.path(path)
        return tuple(sorted({f"{self.method(m)} {canonical_path}" for m in chosen}))
