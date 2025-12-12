from fastapi import APIRouter, Depends

from app.api.deps import get_ai_engine_dep
from app.schemas.ai import AiRequest, AiResponse
from app.services.ai_engine import AiEngine

router = APIRouter()


@router.post(
    "/ai/mock-chat",
    response_model=AiResponse,
    summary="AI mock chat endpoint",
    description=(
        "Endpoint di test per il cervello AI. "
        "Non chiama ancora modelli reali, ma ritorna una risposta mock "
        "contenente tenant, skill, query e info di debug."
    ),
)
def ai_mock_chat(
    payload: AiRequest,
    engine: AiEngine = Depends(get_ai_engine_dep),
) -> AiResponse:
    """
    Esegue una 'conversazione' mock con l'AiEngine.
    """
    return engine.mock_chat(payload)
