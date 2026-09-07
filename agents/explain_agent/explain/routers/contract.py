from explain.dependencies import get_contract_writer
from explain.models.contract_model import ContractRequest, ContractResponse
from explain.services.contract.contract_writer import ContractWriter
from fastapi import APIRouter, Depends

router = APIRouter(tags=["contract"])


@router.post("/contract", response_model=ContractResponse)
def contract(
    request: ContractRequest,
    writer: ContractWriter = Depends(get_contract_writer),
) -> ContractResponse:
    return ContractResponse(contract=writer.write(request))
