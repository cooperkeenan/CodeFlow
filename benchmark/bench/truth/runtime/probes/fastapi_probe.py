"""Ask a FastAPI/Starlette app what it actually registers.

Runs inside the TARGET repository's virtualenv as a standalone script. It must
never import anything from the benchmark package, and it must never import
CodeFlow: its whole value is that it reports the framework's own answer.

Result JSON is written to a file rather than stdout, because importing an
application routinely prints banners and log lines that would corrupt a stdout
protocol.

Usage: python fastapi_probe.py <source_root> <module:attr> <output_json>
"""

import importlib
import json
import sys
import traceback


def endpoint_name(route: object) -> str:
    endpoint = getattr(route, "endpoint", None)
    if endpoint is None:
        return ""
    module = getattr(endpoint, "__module__", "") or ""
    name = getattr(endpoint, "__qualname__", None) or getattr(endpoint, "__name__", "") or ""
    return f"{module}.{name}" if module and name else name


def module_file(route: object) -> str:
    """Where the handler is defined, so framework-provided routes (docs, openapi)
    can be separated from the repository's own."""
    endpoint = getattr(route, "endpoint", None)
    module = sys.modules.get(getattr(endpoint, "__module__", "") or "")
    return getattr(module, "__file__", "") or ""


def collect(app: object) -> list[dict]:
    collected: list[dict] = []
    for route in getattr(app, "routes", []):
        path = getattr(route, "path", None)
        if not isinstance(path, str):
            continue
        methods = getattr(route, "methods", None)
        collected.append(
            {
                "path": path,
                "methods": sorted(methods) if methods else [],
                "endpoint": endpoint_name(route),
                "module_file": module_file(route),
            }
        )
    return collected


def main(argv: list[str]) -> int:
    source_root, app_path, output_path = argv[1], argv[2], argv[3]
    sys.path.insert(0, source_root)
    module_name, _, attribute = app_path.partition(":")

    try:
        module = importlib.import_module(module_name)
        app = getattr(module, attribute or "app")
        payload = {"ok": True, "framework": "fastapi", "routes": collect(app)}
    except BaseException:  # noqa: BLE001 - the failure itself is the reportable result
        payload = {"ok": False, "framework": "fastapi", "error": traceback.format_exc()}

    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
