import posixpath


def module_fqn(relpath: str) -> str:
    return relpath.removesuffix(".py").replace("/", ".")


def package_of(relpath: str) -> str:
    return posixpath.dirname(relpath).replace("/", ".")


def is_project_path(name: str, project_modules: frozenset[str]) -> bool:
    if not name:
        return False
    if name in project_modules:
        return True
    prefix = f"{name}."
    return any(module.startswith(prefix) for module in project_modules)


def resolve_absolute(name: str, importing_module_fqn: str, project_modules: frozenset[str]) -> str:
    if not name:
        return "ext:"
    if is_project_path(name, project_modules):
        return name
    parts = importing_module_fqn.split(".")
    for i in range(len(parts) - 1, 0, -1):
        prefix = ".".join(parts[:i])
        candidate = f"{prefix}.{name}"
        if is_project_path(candidate, project_modules):
            return candidate
    return f"ext:{name.split('.')[0]}"
