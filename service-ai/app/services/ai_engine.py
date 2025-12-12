from datetime import datetime, timezone

from app.core.config import Settings, get_settings
from app.schemas.ai import AiRequest, AiResponse


class AiEngine:
    """
    Motore AI principale.
    Per ora implementa solo una logica MOCK, ma la firma è già 'seria'.
    In futuro potremo instradare verso provider diversi (external/local/custom).
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def mock_chat(self, request: AiRequest) -> AiResponse:
        """
        Implementazione mock: non chiama nessun modello reale,
        ma costruisce una risposta che ci permette di verificare wiring,
        multi-tenant e multi-skill.
        """
        now = datetime.now(timezone.utc).isoformat()

        answer = (
            f"[MOCK ANSWER]\n"
            f"- tenant: {request.tenant_id}\n"
            f"- skill: {request.skill}\n"
            f"- locale: {request.locale}\n"
            f"- query: {request.query}\n"
        )

        debug = {
            "timestamp": now,
            "model_name": self.settings.MODEL_NAME,
            "device": self.settings.DEVICE,
            "max_tokens": self.settings.MAX_TOKENS,
        }

        return AiResponse(
            tenant_id=request.tenant_id,
            skill=request.skill,
            answer=answer,
            provider="mock",
            debug=debug,
        )


def get_ai_engine() -> AiEngine:
    """
    Factory per costruire AiEngine con i settings reali.
    Usata nelle dependency di FastAPI.
    """
    settings = get_settings()
    return AiEngine(settings=settings)
