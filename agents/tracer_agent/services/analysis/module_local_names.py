from models.module_record import ModuleRecord


def local_names_of(module: ModuleRecord) -> frozenset[str]:
    names = {fqn.rsplit(".", 1)[-1] for fqn in module.classes}
    names |= {fqn.rsplit(".", 1)[-1] for fqn in module.functions}
    return frozenset(names)
