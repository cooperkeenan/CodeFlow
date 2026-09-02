from fastapi import Request

from gateway.services.progress_tracker import ProgressTracker
from shared.access_token_store.access_token_store import AccessTokenStore
from shared.code_store.code_store import CodeStore
from shared.diagram_edit_store.diagram_edit_store import DiagramEditStore
from shared.explanation_store.explanation_store import ExplanationStore
from shared.repo_map_store.repo_map_store import RepoMapStore
from shared.user_store.user_store import UserStore


def get_progress_tracker(request: Request) -> ProgressTracker:
    return request.app.state.progress_tracker


def get_code_store(request: Request) -> CodeStore:
    return request.app.state.code_store


def get_user_store(request: Request) -> UserStore:
    return request.app.state.user_store


def get_token_store(request: Request) -> AccessTokenStore:
    return request.app.state.token_store


def get_repo_map_store(request: Request) -> RepoMapStore:
    return request.app.state.repo_map_store


def get_explanation_store(request: Request) -> ExplanationStore:
    return request.app.state.explanation_store


def get_diagram_edit_store(request: Request) -> DiagramEditStore:
    return request.app.state.diagram_edit_store
