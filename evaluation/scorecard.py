def print_scorecard(results: dict) -> float:
    print("\n=== CodeFlow Structural Scorecard ===\n")

    mods = results["modules"]
    print(f"{'Modules':<22} score={mods['score']:.0%}")
    if mods["missing"]:
        print(f"  missing : {mods['missing']}")
    if mods["extra"]:
        print(f"  extra   : {mods['extra']}")

    edges = results["edges"]
    print(f"\n{'Cross-module edges':<22} recall={edges['score']:.0%}")
    for pair in edges["missing"]:
        print(f"  MISS: {pair[0]} → {pair[1]}")

    ep = results["entry_points"]
    print(f"\n{'Entry points':<22} recall={ep['score']:.0%}")
    if ep["missing"]:
        print(f"  missing : {ep['missing']}")

    cc = results["component_counts"]
    print(f"\n{'Component counts':<22} in-range={cc['score']:.0%}")
    for d in cc["details"]:
        status = "OK  " if d["ok"] else "MISS"
        print(f"  {status}  {d['module']:<20} {d['actual']:>3}  [{d['min']}–{d['max']}]")

    keys = ("modules", "edges", "entry_points", "component_counts")
    overall = sum(results[k]["score"] for k in keys) / len(keys)
    print(f"\nOverall: {overall:.0%}\n")
    return overall
