import hashlib

import httpx
from gateway.clients.explain_client import ExplainClient

from shared.contract_prompt_version import PROMPT_VERSION
from shared.explanation_store.explanation_store import ExplanationStore
from shared.models.endpoint_contract import ContractParam, EndpointContract
from shared.models.flow_graph import FlowNode

_SEPARATOR = "\x1f"


class EndpointContractResolver:
    def __init__(self, explain_client: ExplainClient, explanation_store: ExplanationStore) -> None:
        self._explain_client = explain_client
        self._store = explanation_store

    async def resolve(
        self,
        entry_id: str,
        node: FlowNode,
        method: str,
        path: str,
        path_params: list[str],
        sources: dict[str, str],
        symbol_context: dict,
        repo: str,
    ) -> EndpointContract:
        fingerprint = self._fingerprint(entry_id, method, path, sources)
        cached = await self._store.get(fingerprint)
        if cached is not None:
            return EndpointContract.model_validate(cached)
        handler_fqn = symbol_context.get("nodes", {}).get(entry_id, "")
        request_payload = {
            "entry_id": entry_id,
            "label": node.label,
            "method": method,
            "path": path,
            "handler_fqn": handler_fqn,
            "path_params": path_params,
            "symbols": self._symbol_payloads(sources, symbol_context),
            "helpers": [],
        }
        try:
            response = await self._explain_client.contract(request_payload)
            contract = EndpointContract.model_validate(response["contract"])
        except (httpx.HTTPError, RuntimeError, KeyError):
            return self._fallback_contract(method, path, path_params)
        await self._store.put(fingerprint, repo, entry_id, contract.model_dump(mode="json"))
        return contract

    def _symbol_payloads(self, sources: dict[str, str], symbol_context: dict) -> list[dict]:
        functions = symbol_context.get("functions", {})
        classes = symbol_context.get("classes", {})
        payloads = []
        for fqn, source in sources.items():
            entry = functions.get(fqn) or classes.get(fqn) or {}
            kind = "class" if fqn in classes else "function"
            payloads.append(
                {
                    "fqn": fqn,
                    "kind": kind,
                    "name": entry.get("name", fqn.rsplit(".", 1)[-1]),
                    "signature": "",
                    "source": source,
                }
            )
        return payloads

    def _fallback_contract(self, method: str, path: str, path_params: list[str]) -> EndpointContract:
        return EndpointContract(
            method=method,
            path=path,
            params=[
                ContractParam(name=name, location="path", required=True) for name in path_params
            ],
            generated=False,
        )

    def _fingerprint(
        self, entry_id: str, method: str, path: str, sources: dict[str, str]
    ) -> str:
        pairs = sorted(sources.items())
        parts = [PROMPT_VERSION, entry_id, method, path]
        for fqn, source in pairs:
            parts.append(fqn)
            parts.append(source)
        return hashlib.sha256(_SEPARATOR.join(parts).encode("utf-8")).hexdigest()
