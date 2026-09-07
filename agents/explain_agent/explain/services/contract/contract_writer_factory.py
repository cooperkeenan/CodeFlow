import anthropic
from explain.helpers.contract_validator import ContractValidator
from explain.services.contract.contract_writer import ContractWriter
from explain.services.contract.heuristic_contract_writer import HeuristicContractWriter
from explain.services.contract.llm_contract_writer import LlmContractWriter


def build_contract_writer(api_key: str) -> ContractWriter:
    fallback = HeuristicContractWriter()
    if not api_key:
        return fallback
    client = anthropic.Anthropic(api_key=api_key)
    return LlmContractWriter(client, fallback, ContractValidator())
