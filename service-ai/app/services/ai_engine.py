# service-ai/app/services/ai_engine.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Optional

import httpx

from app.core.config import Settings, get_settings
from app.schemas.ai import AiRequest, AiResponse


class AiEngine:
    """
    Motore AI principale.

    In core: wiring serio + modalità demo "non banale" senza dipendenze extra.
    In spike/ai-provider-api:
      - chat -> LLM reale (OpenAI) con fallback a mock
      - demo_rag -> retrieval + LLM reale (OpenAI) se key presente, altrimenti fallback deterministico
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        # Mini knowledge base "demo" (per retrieval deterministico stile RAG).
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
        self._kb_by_id: Dict[str, Dict[str, Any]] = {d["id"]: d for d in self._demo_kb}

    # -------------------------
    # Public entry point
    # -------------------------
    def chat(self, request: AiRequest) -> AiResponse:
        """
        Entry point unico usato da /v1/ai/chat.

        - mock / chat_mock -> mock
        - chat             -> OpenAI reale se OPENAI_API_KEY presente, fallback a mock
        - demo_rag         -> (API branch) retrieval + LLM reale se OPENAI_API_KEY presente
                              fallback a retrieval deterministico se manca la key
        """
        skill = (request.skill or "").strip().lower()

        if skill in {"mock", "mock_chat", "chat_mock"}:
            return self.mock_chat(request)

        if skill in {"chat"}:
            return self._chat_with_optional_llm(request)

        if skill in {"demo_rag", "rag_demo", "faq_demo"}:
            return self._demo_rag_with_optional_llm(request)

        return self.mock_chat(request)

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

    # -------------------------
    # chat (OpenAI) + fallback
    # -------------------------
    def _chat_with_optional_llm(self, request: AiRequest) -> AiResponse:
        """
        Se OPENAI_API_KEY è configurata => usiamo LLM reale.
        Altrimenti fallback al mock.
        """
        if (self.settings.OPENAI_API_KEY or "").strip():
            return self._api_chat_openai(request)

        fallback = self.mock_chat(request)
        if fallback.debug is None:
            fallback.debug = {}
        if isinstance(fallback.debug, dict):
            fallback.debug["provider_step"] = "api (openai) -> fallback (mock; missing key)"
            fallback.debug["model"] = self.settings.OPENAI_MODEL
        return fallback

    def _api_chat_openai(self, request: AiRequest) -> AiResponse:
        """
        Chat LLM via OpenAI Responses API.

        NOTE:
        - rispetta contract AiResponse
        - in caso di errore: fallback al mock con debug.api_error
        """
        now = datetime.now(timezone.utc).isoformat()

        temperature, max_out = self._extract_llm_options(request.metadata)

        instructions = (
            "Sei un assistente AI per una demo tecnica. "
            "Rispondi in italiano, in modo chiaro e professionale. "
            "Se l'utente chiede un confronto o una scelta, motivala in modo pratico."
        )

        user_input = (request.query or "").strip()
        if not user_input:
            user_input = "Scrivi una risposta breve di test (nessun input fornito)."

        try:
            raw = self._openai_responses_call(
                instructions=instructions,
                input_text=user_input,
                temperature=temperature,
                max_output_tokens=max_out,
            )
            answer_text = self._extract_output_text(raw).strip()

            if not answer_text:
                raise RuntimeError("Empty model output")

            debug = {
                "timestamp": now,
                "mode": "api_chat",
                "provider_step": "api (openai)",
                "model": self.settings.OPENAI_MODEL,
                "temperature": temperature,
                "max_output_tokens": max_out,
            }

            return AiResponse(
                tenant_id=request.tenant_id,
                skill=request.skill,
                answer=answer_text,
                provider=f"openai:{self.settings.OPENAI_MODEL}",
                debug=debug,
            )

        except Exception as e:
            fallback = self.mock_chat(request)
            if fallback.debug is None:
                fallback.debug = {}
            if isinstance(fallback.debug, dict):
                fallback.debug["provider_step"] = "api (openai) -> fallback (mock)"
                fallback.debug["api_error"] = str(e)
                fallback.debug["model"] = self.settings.OPENAI_MODEL
            return fallback

    # -------------------------
    # demo_rag (retrieval) + optional LLM
    # -------------------------
    def _demo_rag_with_optional_llm(self, request: AiRequest) -> AiResponse:
        """
        In questa branch: se OPENAI_API_KEY è configurata => usiamo LLM reale con contesto.
        Altrimenti fallback al demo_rag deterministico.
        """
        if (self.settings.OPENAI_API_KEY or "").strip():
            return self._api_rag_openai(request)

        # fallback deterministico
        return self._demo_rag(request, provider_step="core (no-llm)")

    def _demo_rag(self, request: AiRequest, provider_step: str) -> AiResponse:
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
                "provider_step": provider_step,
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
            "provider_step": provider_step,
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

    def _api_rag_openai(self, request: AiRequest) -> AiResponse:
        """
        Retrieval deterministico + generazione LLM via OpenAI Responses API.

        NOTE:
        - rispetta contract AiResponse
        - in caso di errore: fallback al demo_rag deterministico con debug.api_error
        """
        now = datetime.now(timezone.utc).isoformat()

        best_doc, best_score, ranked = self._retrieve_best_doc(request.query)

        if not best_doc:
            return self._demo_rag(request, provider_step="api (openai) -> fallback (no context)")

        # Prendiamo fino a 3 documenti con score > 0 (in ordine ranked)
        selected_docs: List[Dict[str, Any]] = []
        for r in ranked:
            if r.get("score", 0) <= 0:
                continue
            doc = self._kb_by_id.get(r["id"])
            if doc:
                selected_docs.append(doc)
            if len(selected_docs) >= 3:
                break

        context = "\n\n".join(
            f"### {d['title']}\n{d['text']}" for d in selected_docs
        )

        temperature, max_out = self._extract_llm_options(request.metadata)

        instructions = (
            "Sei un assistente AI per una demo tecnica. "
            "Devi rispondere in italiano, in modo chiaro e professionale. "
            "Usa principalmente il CONTEXT fornito. "
            "Se manca informazione nel CONTEXT, dillo esplicitamente e fai un'ipotesi minima."
        )

        user_input = (
            "CONTEXT:\n"
            f"{context}\n\n"
            "USER QUESTION:\n"
            f"{request.query}\n\n"
            "OUTPUT:\n"
            "- Rispondi con 6-10 bullet pratici\n"
            "- Chiudi con una riga: 'Differenza percepibile: ...' (1 frase)\n"
        )

        try:
            raw = self._openai_responses_call(
                instructions=instructions,
                input_text=user_input,
                temperature=temperature,
                max_output_tokens=max_out,
            )
            answer_text = self._extract_output_text(raw).strip()

            if not answer_text:
                raise RuntimeError("Empty model output")

            debug = {
                "timestamp": now,
                "mode": "api_rag",
                "provider_step": "api (openai)",
                "model": self.settings.OPENAI_MODEL,
                "temperature": temperature,
                "max_output_tokens": max_out,
                "best_doc": {"id": best_doc["id"], "title": best_doc["title"]},
                "score": best_score,
                "ranked": ranked[:3],
            }

            return AiResponse(
                tenant_id=request.tenant_id,
                skill=request.skill,
                answer=answer_text,
                provider=f"openai:{self.settings.OPENAI_MODEL}",
                debug=debug,
            )

        except Exception as e:
            fallback = self._demo_rag(request, provider_step="api (openai) -> fallback (demo_rag)")
            if fallback.debug is None:
                fallback.debug = {}
            if isinstance(fallback.debug, dict):
                fallback.debug["api_error"] = str(e)
                fallback.debug["model"] = self.settings.OPENAI_MODEL
            return fallback

    # -------------------------
    # OpenAI Responses API helpers
    # -------------------------
    def _openai_responses_call(
        self,
        instructions: str,
        input_text: str,
        temperature: float,
        max_output_tokens: int,
    ) -> Dict[str, Any]:
        """
        Chiamata sincrona a OpenAI Responses API:
        POST /v1/responses con model + instructions + input
        """
        base_url = (self.settings.OPENAI_BASE_URL or "https://api.openai.com/v1").rstrip("/")
        url = f"{base_url}/responses"

        api_key = (self.settings.OPENAI_API_KEY or "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not configured")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.settings.OPENAI_MODEL,
            "instructions": instructions,
            "input": input_text,
            "temperature": float(temperature),
            "max_output_tokens": int(max_output_tokens),
            "store": False,
        }

        timeout = httpx.Timeout(float(self.settings.OPENAI_TIMEOUT_SEC))
        with httpx.Client(timeout=timeout) as client:
            r = client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            return r.json()

    def _extract_output_text(self, data: Dict[str, Any]) -> str:
        """
        Estrae testo in modo robusto:
        - se esiste output_text top-level, usa quello
        - altrimenti scansiona output[].content[].text
        """
        if isinstance(data.get("output_text"), str) and data["output_text"].strip():
            return data["output_text"]

        out = data.get("output")
        if not isinstance(out, list):
            return ""

        chunks: List[str] = []
        for item in out:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "message":
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for c in content:
                if not isinstance(c, dict):
                    continue
                if isinstance(c.get("text"), str) and c.get("text"):
                    chunks.append(c["text"])

        return "\n".join(chunks).strip()

    # -------------------------
    # Retrieval helpers
    # -------------------------
    def _retrieve_best_doc(
        self, query: str
    ) -> Tuple[Optional[Dict[str, Any]], int, List[Dict[str, Any]]]:
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return None, 0, []

        ranked: List[Dict[str, Any]] = []
        best_doc: Optional[Dict[str, Any]] = None
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

    def _extract_llm_options(self, metadata: Any) -> Tuple[float, int]:
        """
        Legge metadata.options = { temperature, max_tokens } dal client (se presente),
        altrimenti usa defaults dai settings.
        """
        temperature = float(self.settings.OPENAI_TEMPERATURE)
        max_out = int(self.settings.OPENAI_MAX_OUTPUT_TOKENS)

        if isinstance(metadata, dict):
            opts = metadata.get("options")
            if isinstance(opts, dict):
                t = opts.get("temperature")
                m = opts.get("max_tokens")
                if isinstance(t, (int, float)):
                    temperature = float(t)
                if isinstance(m, int):
                    max_out = int(m)

        if temperature < 0:
            temperature = 0.0
        if temperature > 2:
            temperature = 2.0
        if max_out < 16:
            max_out = 16
        if max_out > 2048:
            max_out = 2048

        return temperature, max_out


def get_ai_engine() -> AiEngine:
    settings = get_settings()
    return AiEngine(settings=settings)
