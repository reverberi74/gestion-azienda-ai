from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AiRequest(BaseModel):
    """
    Input generico per una richiesta AI multi-tenant/multi-skill.
    """

    tenant_id: str = Field(
        ...,
        description="Identificatore univoco del tenant/cliente (es. comune_noto, studio_rossi, ...).",
    )
    skill: str = Field(
        ...,
        description=(
            "Nome della 'skill' AI da eseguire (es. faq_municipality, "
            "ticket_classifier_legal, appointment_helper_dentist, ...)."
        ),
    )
    query: str = Field(
        ...,
        description="Testo principale della richiesta (domanda dell'utente o contenuto da analizzare).",
    )
    locale: Optional[str] = Field(
        "it-IT",
        description="Codice lingua/locale (es. it-IT, en-US).",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadati opzionali (id utente, canale, contesto applicativo, ecc.).",
    )


class AiResponse(BaseModel):
    """
    Output standardizzato dell'AI service.
    """

    tenant_id: str = Field(..., description="Tenant a cui appartiene la risposta.")
    skill: str = Field(..., description="Skill che ha generato la risposta.")
    answer: str = Field(..., description="Testo della risposta generata (mock o reale).")
    provider: str = Field(
        "mock",
        description="Nome del provider usato (mock, external, local, custom, ...).",
    )
    debug: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Informazioni di debug/firma tecnica (modello, timestamp, ecc.).",
    )
