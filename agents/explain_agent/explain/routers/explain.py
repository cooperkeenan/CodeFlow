from explain.dependencies import get_symbol_explainer
from explain.models.explain_model import ExplainRequest, ExplainResponse
from explain.services.explanation.symbol_explainer import SymbolExplainer
from fastapi import APIRouter, Depends

router = APIRouter(tags=["explain"])


@router.post("/explain", response_model=ExplainResponse)
def explain(
    request: ExplainRequest,
    explainer: SymbolExplainer = Depends(get_symbol_explainer),
) -> ExplainResponse:
    return ExplainResponse(explanation=explainer.explain(request))
