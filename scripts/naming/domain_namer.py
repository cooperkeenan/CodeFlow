class DomainNamer:
    def __init__(self, tld: str = "com") -> None:
        self._tld = tld.lstrip(".").lower()

    @property
    def tld(self) -> str:
        return self._tld

    def domain_for(self, name: str) -> str:
        return f"{name.lower()}.{self._tld}"
