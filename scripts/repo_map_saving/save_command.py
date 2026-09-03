import asyncio
import os

from repo_map_saving.repo_map_saver import RepoMapSaver
from shared.models.diagram_template import RenderedView
from shared.models.flow_graph import FlowGraph
from shared.repo_map_store.neon_repo_map_store import NeonRepoMapStore
from repo_map_saving.user_handle_resolver import UserHandleResolver

_SAVE_SOURCE = "ci-local"


def parse_save_flag(argv: list[str]) -> tuple[str | None, list[str]]:
    handle: str | None = None
    remaining: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == "--save":
            handle = argv[i + 1]
            i += 2
            continue
        remaining.append(argv[i])
        i += 1
    return handle, remaining


def save_to_account(repo: str, graph: FlowGraph, view: RenderedView, handle: str) -> int:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL is not set; cannot save")
        return 1
    try:
        user_id = UserHandleResolver(database_url).resolve(handle)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    saver = RepoMapSaver(NeonRepoMapStore(database_url))
    try:
        asyncio.run(saver.save(user_id, repo, graph, view, _SAVE_SOURCE))
    except Exception as exc:
        print(f"ERROR: failed to save '{repo}' for '{handle}': {exc}")
        return 1
    print(f"Saved '{repo}' to account '{handle}'")
    return 0
