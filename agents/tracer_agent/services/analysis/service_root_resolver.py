class ServiceRootResolver:
    def __init__(
        self,
        service_hints: frozenset[str] | None = None,
        source_roots: frozenset[str] = frozenset(),
    ) -> None:
        self._hints = service_hints or frozenset()
        self._roots = source_roots

    def root_of(self, fqn: str) -> str:
        hint = self._longest_match(fqn, self._hints)
        if hint is not None:
            return hint
        derived = self._longest_match(fqn, self._roots)
        if derived is not None:
            return derived
        parts = fqn.split(".")
        if parts[0] == "agents" and len(parts) >= 2:
            return f"{parts[0]}.{parts[1]}"
        return parts[0]

    def _longest_match(self, fqn: str, candidates: frozenset[str]) -> str | None:
        matches = [c for c in candidates if fqn == c or fqn.startswith(f"{c}.")]
        if not matches:
            return None
        return max(matches, key=len)
