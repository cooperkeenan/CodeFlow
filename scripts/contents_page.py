from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "agents" / "tracer_agent"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from contents_rules import CallGraph, symbol
from render_repo import read_python_sources
from tracer.services.analysis.indexing.factory import build_project_indexer
from tracer.services.analysis.resolve.call_resolver import CallResolver


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo")
    parser.add_argument("--out")
    args = parser.parse_args()
    target = Path(args.repo).expanduser().resolve()
    started = time.perf_counter()
    files = read_python_sources(target)
    index = build_project_indexer().index(files)
    indexed = time.perf_counter()
    sites = CallResolver(index).resolve_project()
    resolved = time.perf_counter()
    graph = CallGraph.build(index.functions, sites)
    flows = graph.flows()
    symbols = [symbol(f, index.functions[f]) for f in sorted(index.functions, key=graph.sort_key)]
    text = json.dumps(
        {"repo": target.name, "flows": flows, "symbols": symbols}, indent=1, sort_keys=True
    )
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    else:
        sys.stdout.write(text + "\n")
    print(
        f"contents: files={len(files)} functions={len(index.functions)} flows={len(flows)} "
        f"index={indexed - started:.2f}s resolve={resolved - indexed:.2f}s",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
