from dataclasses import dataclass, field

from shared.models.flow_graph import EffectKind


@dataclass(frozen=True)
class LibraryRule:
    roots: frozenset[str]
    kind: EffectKind
    target: str
    methods: frozenset[str] = field(default_factory=frozenset)
    method_prefix: str = ""


RULES: tuple[LibraryRule, ...] = (
    LibraryRule(
        frozenset({"httpx", "requests", "aiohttp"}),
        "http_out",
        "url",
        frozenset({"get", "post", "put", "delete", "patch", "request"}),
    ),
    LibraryRule(frozenset({"anthropic", "openai"}), "llm", "model", frozenset({"create"})),
    LibraryRule(
        frozenset({"psycopg", "psycopg_pool", "asyncpg", "sqlalchemy", "databases"}),
        "database",
        "sql",
        frozenset(
            {"execute", "executemany", "fetch", "fetchrow", "fetchval", "fetchall", "fetchone", "connect"}
        ),
    ),
    LibraryRule(
        frozenset({"smtplib", "sendgrid", "resend"}),
        "email",
        "none",
        frozenset({"send", "send_message", "sendmail", "send_email"}),
    ),
    LibraryRule(frozenset({"boto3", "aioboto3"}), "queue", "boto"),
    LibraryRule(frozenset({"builtins"}), "file", "path", frozenset({"open"})),
    LibraryRule(frozenset({"pathlib"}), "file", "path", method_prefix="write_"),
)

BOTO_METHOD_KINDS: dict[str, EffectKind] = {
    "send_message": "queue",
    "receive_message": "queue",
    "publish": "queue",
    "put_object": "file",
    "get_object": "file",
    "upload_file": "file",
    "download_file": "file",
}

ROUTE_VERBS: frozenset[str] = frozenset({"get", "post", "put", "delete", "patch", "head", "options"})
