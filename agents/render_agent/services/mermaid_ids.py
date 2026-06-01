def node_id(name: str) -> str:
    return (
        name.replace(" ", "_")
            .replace("-", "_")
            .replace("/", "_")
            .replace(".", "_")
    )
