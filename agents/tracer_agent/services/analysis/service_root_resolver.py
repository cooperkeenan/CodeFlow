class ServiceRootResolver:
    def __init__(self, service_hints: frozenset[str] | None = None) -> None:
        self._hints = service_hints or frozenset()

    def root_of(self, fqn: str) -> str:
        hint = self._hint_root(fqn)
        if hint is not None:
            return hint
        parts = fqn.split(".")
        if parts[0] == "agents" and len(parts) >= 2:
            return f"{parts[0]}.{parts[1]}"
        return parts[0]

    def _hint_root(self, fqn: str) -> str | None:
        matches = [h for h in self._hints if fqn == h or fqn.startswith(f"{h}.")]
        if not matches:
            return None
        return max(matches, key=len)
