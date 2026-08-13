"""Ask Django's own URL resolver what routes are registered.

Runs inside the TARGET repository's virtualenv as a standalone script. Never
imports the benchmark package and never imports CodeFlow: the whole point is that
this reports the framework's answer, not anyone's approximation of it.

Usage: python django_probe.py <source_root> <settings_module> <output_json>
Extra sys.path entries come from BENCH_PROBE_SYS_PATHS (os.pathsep separated).
"""

import json
import os
import sys
import traceback


def method_names(callback: object) -> list[str]:
    """HTTP methods a view actually implements.

    A Django URLconf does not declare methods, so a function-based view yields
    nothing and the route is treated as method-agnostic downstream. Guessing GET
    would invent ground truth.
    """
    view_class = getattr(callback, "view_class", None)
    if view_class is None:
        return []
    declared = getattr(view_class, "http_method_names", []) or []
    return sorted(
        name.upper() for name in declared if callable(getattr(view_class, name, None))
    )


def endpoint_name(callback: object) -> str:
    view_class = getattr(callback, "view_class", None)
    target = view_class if view_class is not None else callback
    module = getattr(target, "__module__", "") or ""
    name = getattr(target, "__qualname__", None) or getattr(target, "__name__", "") or ""
    return f"{module}.{name}" if module and name else name


def module_file(callback: object) -> str:
    """Where the handler is defined, so routes owned by third-party packages
    (django.contrib.admin and friends) can be separated from the repo's own."""
    view_class = getattr(callback, "view_class", None)
    target = view_class if view_class is not None else callback
    module = sys.modules.get(getattr(target, "__module__", "") or "")
    return getattr(module, "__file__", "") or ""


def walk(resolver: object, prefix: str, collected: list[dict], seen: set[int]) -> None:
    from django.urls.resolvers import URLPattern, URLResolver

    for entry in getattr(resolver, "url_patterns", []):
        pattern = prefix + str(entry.pattern)
        if isinstance(entry, URLResolver):
            if id(entry) in seen:
                continue
            seen.add(id(entry))
            walk(entry, pattern, collected, seen)
        elif isinstance(entry, URLPattern):
            collected.append(
                {
                    "path": pattern,
                    "methods": method_names(entry.callback),
                    "endpoint": endpoint_name(entry.callback),
                    "module_file": module_file(entry.callback),
                }
            )


def main(argv: list[str]) -> int:
    source_root, settings_module, output_path = argv[1], argv[2], argv[3]
    for entry in reversed(
        [source_root, *os.environ.get("BENCH_PROBE_SYS_PATHS", "").split(os.pathsep)]
    ):
        if entry:
            sys.path.insert(0, entry)

    try:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
        import django

        django.setup()
        from django.urls import get_resolver

        collected: list[dict] = []
        walk(get_resolver(), "", collected, set())
        payload = {"ok": True, "framework": "django", "routes": collected}
    except BaseException:  # noqa: BLE001 - the failure itself is the reportable result
        payload = {"ok": False, "framework": "django", "error": traceback.format_exc()}

    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
