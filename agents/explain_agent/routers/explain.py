from fastapi import APIRouter, Depends

from dependencies import get_symbol_explainer
from models.explain_model import ExplainRequest, ExplainResponse
from services.explanation.symbol_explainer import SymbolExplainer

router = APIRouter(tags=["explain"])


@router.post("/explain", response_model=ExplainResponse)
def explain(
    request: ExplainRequest,
    explainer: SymbolExplainer = Depends(get_symbol_explainer),
) -> ExplainResponse:
    return ExplainResponse(explanation=explainer.explain(request))
