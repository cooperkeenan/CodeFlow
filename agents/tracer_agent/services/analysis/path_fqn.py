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


def agent_root_of(importing_module_fqn: str) -> str | None:
    parts = importing_module_fqn.split(".")
    if len(parts) >= 2 and parts[0] == "agents":
        return f"{parts[0]}.{parts[1]}"
    return None


def resolve_absolute(name: str, importing_module_fqn: str, project_modules: frozenset[str]) -> str:
    if is_project_path(name, project_modules):
        return name
    root = agent_root_of(importing_module_fqn)
    if root is not None:
        candidate = f"{root}.{name}"
        if is_project_path(candidate, project_modules):
            return candidate
    return f"ext:{name.split('.')[0]}" if name else "ext:"
