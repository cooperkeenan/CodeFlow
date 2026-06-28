class BreadcrumbBuilder:
    _MAX_NAMES = 15

    def build(self, processed_raws: list[dict], current_label: str) -> str:
        names: list[str] = []
        seen: set[str] = set()
        for raw in processed_raws:
            for comp in raw.get("components", []):
                name = comp.get("name") if isinstance(comp, dict) else None
                if name and name not in seen:
                    seen.add(name)
                    names.append(name)
                    if len(names) >= self._MAX_NAMES:
                        break
            if len(names) >= self._MAX_NAMES:
                break
        names_str = ", ".join(names) if names else "none"
        return f"Previously traced: {names_str}. Continuing from: {current_label}."
