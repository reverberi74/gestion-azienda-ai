from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from app.core.config import Settings, get_settings
from app.schemas.ai import AiRequest, AiResponse


class AiEngine:
    """
    Motore AI principale.
    In core: wiring serio + modalità demo "non banale" senza dipendenze extra.
    Nei provider spike (api/prebuilt/custom) sostituiremo l'implementazione interna.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        # Mini knowledge base "demo" per far vedere una differenza percepibile già nello spike core.
        # (Niente modelli: scoring deterministico su overlap termini -> stile RAG)
        self._demo_kb: List[Dict[str, Any]] = [
            {
                "id": "branching_strategy",
                "title": "Strategia branch spike vs feature",
                "text": (
                    "Gli spike sono rami di laboratorio (spike/...) che non vanno mergiati su development. "
                    "Servono a testare integrazioni e confrontare approcci senza sporcare il core stabile. "
                    "Se qualcosa torna utile, si fa cherry-pick mirato sul ramo reale."
                ),
            },
            {
                "id": "three_scenarios",
                "title": "Tre scenari AI da confrontare",
                "text": (
                    "Scenario API esterna: latenza dipende dalla rete, setup veloce, costi a consumo, "
                    "dati potenzialmente fuori azienda. "
                    "Scenario prebuilt locale: setup medio, modello on-prem, latenza più stabile, "
                    "richiede CPU/GPU e gestione dipendenze. "
                    "Scenario custom: massima flessibilità (fine-tune/LoRA), costo e complessità maggiori, "
                    "migliore adattabilità al dominio."
                ),
            },
            {
                "id": "contract",
                "title": "Contract unico end-to-end",
                "text": (
                    "Un endpoint unico /ai/chat con payload standardizzato permette di cambiare provider "
                    "senza cambiare FE/BE. Le differenze si misurano in latency, startup time, gestione errori, "
                    "costi e requisiti infrastrutturali."
                ),
            },
        ]

    def mock_chat(self, request: AiRequest) -> AiResponse:
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
            "mode": "mock",
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

    def chat(self, request: AiRequest) -> AiResponse:
        """
        Entry point unico usato da /v1/ai/chat.
        In core gestiamo:
        - chat/mock (semplice)
        - demo_rag (risposta "più intelligente" senza modelli)
        """
        skill = (request.skill or "").strip().lower()

        if skill in {"demo_rag", "rag_demo", "faq_demo"}:
            return self._demo_rag(request)

        # default: mock
        return self.mock_chat(request)

    def _demo_rag(self, request: AiRequest) -> AiResponse:
        """
        Mini retrieval deterministico:
        - tokenizza query
        - score per overlap con documenti KB
        - risponde con estratto + spiegazione (stile "rag")
        """
        now = datetime.now(timezone.utc).isoformat()

        best_doc, best_score, ranked = self._retrieve_best_doc(request.query)

        if not best_doc:
            answer = (
                "Non ho trovato un contesto rilevante nella knowledge base demo.\n"
                "Prova con parole chiave come: 'spike', 'provider', 'api', 'prebuilt', 'custom', 'contract'."
            )
            debug = {
                "timestamp": now,
                "mode": "demo_rag",
                "kb_size": len(self._demo_kb),
                "ranked": ranked[:3],
            }
            return AiResponse(
                tenant_id=request.tenant_id,
                skill=request.skill,
                answer=answer,
                provider="demo-rag",
                debug=debug,
            )

        answer = (
            "[DEMO RAG]\n"
            f"Ho selezionato il contesto più rilevante: **{best_doc['title']}**\n\n"
            f"✅ Risposta (basata su contesto interno):\n{best_doc['text']}\n\n"
            "📌 Nota: nello spike core questo è un retrieval deterministico (senza LLM). "
            "Nel provider API, la stessa base verrà usata con un LLM reale per generare una risposta più naturale.\n"
        )

        debug = {
            "timestamp": now,
            "mode": "demo_rag",
            "provider_step": "core (no-llm)",
            "best_doc": {"id": best_doc["id"], "title": best_doc["title"]},
            "score": best_score,
            "ranked": ranked[:3],
        }

        return AiResponse(
            tenant_id=request.tenant_id,
            skill=request.skill,
            answer=answer,
            provider="demo-rag",
            debug=debug,
        )

    def _retrieve_best_doc(self, query: str) -> Tuple[Dict[str, Any] | None, int, List[Dict[str, Any]]]:
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return None, 0, []

        ranked: List[Dict[str, Any]] = []
        best_doc = None
        best_score = -1

        for doc in self._demo_kb:
            d_tokens = self._tokenize(doc["text"] + " " + doc["title"])
            score = len(q_tokens.intersection(d_tokens))
            ranked.append({"id": doc["id"], "title": doc["title"], "score": score})

            if score > best_score:
                best_score = score
                best_doc = doc

        ranked.sort(key=lambda x: x["score"], reverse=True)

        if best_score <= 0:
            return None, 0, ranked

        return best_doc, best_score, ranked

    def _tokenize(self, text: str) -> set[str]:
        if not text:
            return set()
        cleaned = "".join(ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in text)
        parts = [p for p in cleaned.split() if len(p) >= 3]
        return set(parts)


def get_ai_engine() -> AiEngine:
    settings = get_settings()
    return AiEngine(settings=settings)
