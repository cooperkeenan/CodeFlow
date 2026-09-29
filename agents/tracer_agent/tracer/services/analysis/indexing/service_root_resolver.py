class ServiceRootResolver:
    def __init__(
        self,
        service_hints: frozenset[str] | None = None,
        source_roots: frozenset[str] = frozenset(),
        app_roots: frozenset[str] = frozenset(),
    ) -> None:
        self._hints = service_hints or frozenset()
        self._roots = source_roots
        self._app_roots = app_roots

    def root_of(self, fqn: str) -> str:
        hint = self._longest_match(fqn, self._hints)
        if hint is not None:
            return hint
        app_root = self._longest_match(fqn, self._app_roots)
        if app_root is not None:
            return app_root
        derived = self._longest_match(fqn, self._roots)
        if derived is not None:
            return derived
        return fqn.split(".")[0]

    def _longest_match(self, fqn: str, candidates: frozenset[str]) -> str | None:
        matches = [c for c in candidates if fqn == c or fqn.startswith(f"{c}.")]
        if not matches:
            return None
        return max(matches, key=len)
