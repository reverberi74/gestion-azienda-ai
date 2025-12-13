import time
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.deps import get_ai_engine_dep, get_settings_dep
from app.core.config import Settings
from app.schemas.ai import AiRequest, AiResponse
from app.services.ai_engine import AiEngine

router = APIRouter()


def _require_internal_token(
    settings: Settings,
    x_ai_internal_token: Optional[str],
) -> None:
    expected = (settings.AI_INTERNAL_TOKEN or "").strip()

    # Se non è configurato, per sicurezza consideriamo comunque richiesto (qui siamo in spike B)
    if not expected:
        raise HTTPException(status_code=500, detail="AI_INTERNAL_TOKEN not configured")

    if not x_ai_internal_token or x_ai_internal_token.strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid internal token")


@router.post(
    "/ai/chat",
    response_model=AiResponse,
    summary="AI chat endpoint (core contract)",
    description=(
        "Endpoint stabile per wiring end-to-end. "
        "In spike core usa modalità mock / demo_rag (no LLM). "
        "Nei provider spike verrà collegato a provider reali."
    ),
)
def ai_chat(
    payload: AiRequest,
    engine: AiEngine = Depends(get_ai_engine_dep),
    settings: Settings = Depends(get_settings_dep),
    x_ai_internal_token: Optional[str] = Header(default=None, alias="X-AI-Internal-Token"),
) -> AiResponse:
    _require_internal_token(settings, x_ai_internal_token)

    t0 = time.perf_counter()
    res = engine.chat(payload)
    dt_ms = int((time.perf_counter() - t0) * 1000)

    # arricchiamo debug senza rompere schema
    if res.debug is None:
        res.debug = {}
    if isinstance(res.debug, dict):
        res.debug["latency_ms"] = dt_ms

    return res


@router.post(
    "/ai/mock-chat",
    response_model=AiResponse,
    summary="AI mock chat endpoint (legacy demo)",
    description=(
        "Endpoint storico di test. Resta per compatibilità, ma lo spike core usa /ai/chat."
    ),
)
def ai_mock_chat(
    payload: AiRequest,
    engine: AiEngine = Depends(get_ai_engine_dep),
) -> AiResponse:
    return engine.mock_chat(payload)
