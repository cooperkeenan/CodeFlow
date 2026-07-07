import hashlib
import secrets


class TokenHasher:
    def mint(self, prefix: str) -> tuple[str, str, str]:
        body = secrets.token_urlsafe(32)
        raw = f"{prefix}{body}"
        return raw, self.hash(raw), raw[: len(prefix) + 8]

    def hash(self, raw: str) -> str:
        return hashlib.sha256(raw.encode()).hexdigest()
