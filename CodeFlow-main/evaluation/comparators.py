from evaluation.answer_sheet.schema import AnswerSheet


def compare_modules(spec: dict, fixture: AnswerSheet) -> dict:
    found = {m["name"] for m in spec.get("modules", [])}
    expected = set(fixture.modules)
    correct = found & expected
    precision = len(correct) / len(found) if found else 0.0
    recall = len(correct) / len(expected) if expected else 1.0
    return {
        "score": (precision + recall) / 2,
        "found": sorted(found),
        "missing": sorted(expected - found),
        "extra": sorted(found - expected),
    }


def compare_edges(spec: dict, fixture: AnswerSheet) -> dict:
    comp_to_mod: dict[str, str] = {}
    for m in spec.get("modules", []):
        for comps in m.get("zones", {}).values():
            for c in comps:
                comp_to_mod[c["name"]] = m["name"]
    found_pairs: set[tuple[str, str]] = set()
    for e in spec.get("edges", []):
        sm = comp_to_mod.get(e["source"])
        tm = comp_to_mod.get(e["target"])
        if sm and tm and sm != tm:
            found_pairs.add((sm, tm))
    expected_pairs = {(e.source_module, e.target_module) for e in fixture.expected_cross_module_edges}
    correct = found_pairs & expected_pairs
    recall = len(correct) / len(expected_pairs) if expected_pairs else 1.0
    return {
        "score": recall,
        "found": sorted(found_pairs),
        "missing": sorted(expected_pairs - found_pairs),
    }


def compare_entry_points(spec: dict, fixture: AnswerSheet) -> dict:
    all_names = {
        c["name"]
        for m in spec.get("modules", [])
        for cs in m.get("zones", {}).values()
        for c in cs
    }
    spec_entries = set(spec.get("entry_points", []))
    expected = set(fixture.orchestrators) | set(fixture.entry_points)
    found = expected & (all_names | spec_entries)
    score = len(found) / len(expected) if expected else 1.0
    return {
        "score": score,
        "found": sorted(found),
        "missing": sorted(expected - found),
    }


def compare_component_counts(spec: dict, fixture: AnswerSheet) -> dict:
    counts = {
        m["name"]: sum(len(cs) for cs in m.get("zones", {}).values())
        for m in spec.get("modules", [])
    }
    details = []
    in_range = 0
    for r in fixture.component_count_ranges:
        actual = counts.get(r.module, 0)
        ok = r.min <= actual <= r.max
        if ok:
            in_range += 1
        details.append({"module": r.module, "actual": actual, "min": r.min, "max": r.max, "ok": ok})
    total = len(details)
    return {"score": in_range / total if total else 1.0, "details": details}
