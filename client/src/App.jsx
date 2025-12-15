// client/src/App.jsx

import { useEffect, useMemo, useRef, useState } from "react";

const COOLDOWN_SECONDS = 22;

function App() {
  // Health
  const [status, setStatus] = useState(null);
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [errorHealth, setErrorHealth] = useState(null);

  // AI Playground
  const [tenantId, setTenantId] = useState("playground");
  const [skill, setSkill] = useState("demo_rag");
  const [query, setQuery] = useState("Scrivi una risposta di test: perché usare branch spike?");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState(null);
  const [aiResponse, setAiResponse] = useState(null);

  // Cache toggle (default: demo_rag ON, chat OFF)
  const [useCache, setUseCache] = useState(true);

  // Anti-429 cooldown + cache
  const [cooldownLeft, setCooldownLeft] = useState(0);
  const cooldownTimerRef = useRef(null);
  const cacheRef = useRef(new Map()); // key -> response

  const payload = useMemo(
    () => ({
      tenant_id: tenantId,
      skill,
      query,
      locale: "it-IT",
      metadata: {
        source: "ai-playground",
        options: { temperature: 0.2, max_tokens: 220 },
      },
    }),
    [tenantId, skill, query]
  );

  const cacheKey = useMemo(() => {
    try {
      return JSON.stringify(payload);
    } catch {
      return `${tenantId}::${skill}::${query}`;
    }
  }, [payload, tenantId, skill, query]);

  const skillLower = (skill || "").toLowerCase();
  const isPotentiallyOpenAi = skillLower === "demo_rag" || skillLower === "chat";

  // Default cache behavior by skill
  useEffect(() => {
    if (skillLower === "chat") setUseCache(false);
    else if (skillLower === "demo_rag") setUseCache(true);
    else setUseCache(false);
  }, [skillLower]);

  useEffect(() => {
    async function loadHealth() {
      try {
        setLoadingHealth(true);
        setErrorHealth(null);

        const res = await fetch("/api/v1/health");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        setStatus(data);
      } catch (err) {
        setErrorHealth(err?.message || "Errore sconosciuto");
      } finally {
        setLoadingHealth(false);
      }
    }

    loadHealth();
  }, []);

  // Cooldown ticker
  useEffect(() => {
    if (cooldownLeft <= 0) {
      if (cooldownTimerRef.current) {
        clearInterval(cooldownTimerRef.current);
        cooldownTimerRef.current = null;
      }
      return;
    }

    if (!cooldownTimerRef.current) {
      cooldownTimerRef.current = setInterval(() => {
        setCooldownLeft((s) => Math.max(0, s - 1));
      }, 1000);
    }
  }, [cooldownLeft]);

  function startCooldownIfNeeded() {
    if (!isPotentiallyOpenAi) return;
    setCooldownLeft(COOLDOWN_SECONDS);
  }

  function normalizeError(resStatus, data) {
    const beMsg =
      data?.error?.message ||
      data?.message ||
      (typeof data === "string" ? data : null);

    const nestedStatus =
      data?.error?.http_status ?? data?.error?.status ?? data?.status ?? null;

    const detailStr =
      String(data?.error?.details?.detail || "") +
      " " +
      String(data?.error?.details?.error || "") +
      " " +
      String(data?.detail || "");

    const isRateLimit =
      resStatus === 429 ||
      nestedStatus === 429 ||
      detailStr.toLowerCase().includes("too many") ||
      detailStr.toLowerCase().includes("rate limit") ||
      detailStr.toLowerCase().includes("rate");

    if (isRateLimit) {
      return `Rate limit (free tier). Attendi ~${COOLDOWN_SECONDS}s e riprova.`;
    }

    if (resStatus === 422 && data?.errors) {
      const firstField = Object.keys(data.errors)[0];
      const firstMsg = data.errors?.[firstField]?.[0];
      return firstMsg || "Validazione fallita (422).";
    }

    return beMsg || `HTTP ${resStatus}`;
  }

  function clearCache() {
    cacheRef.current = new Map();
    // feedback UI (soft)
    setAiError(null);
    setAiResponse((prev) =>
      prev
        ? {
            ...prev,
            debug: { ...(prev?.debug || {}), cache_cleared: true },
          }
        : prev
    );
  }

  async function runAi(e) {
    e?.preventDefault?.();

    if (isPotentiallyOpenAi && cooldownLeft > 0) {
      setAiError(`Cooldown attivo. Attendi ${cooldownLeft}s per evitare 429.`);
      return;
    }

    // cache hit (solo se abilitata)
    if (useCache) {
      const cached = cacheRef.current.get(cacheKey);
      if (cached) {
        setAiError(null);
        setAiResponse({
          ...cached,
          debug: {
            ...(cached?.debug || {}),
            cached: true,
            cache_key: cacheKey,
          },
        });
        return;
      }
    }

    try {
      setAiLoading(true);
      setAiError(null);
      setAiResponse(null);

      // avvio cooldown subito (evita spam click su provider “costoso”)
      startCooldownIfNeeded();

      const res = await fetch("/api/v1/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => null);

      if (!res.ok) {
        const msg = normalizeError(res.status, data);
        throw new Error(msg);
      }

      // salva in cache solo se abilitata
      if (useCache) {
        cacheRef.current.set(cacheKey, data);
      }

      const enriched = {
        ...data,
        debug: {
          ...(data?.debug || {}),
          cached: false,
          cache_enabled: !!useCache,
        },
      };

      setAiResponse(enriched);
    } catch (err) {
      setAiError(err?.message || "Errore sconosciuto");
    } finally {
      setAiLoading(false);
    }
  }

  const provider = aiResponse?.provider;
  const latencyMs =
    aiResponse?.debug?.latency_ms != null ? aiResponse.debug.latency_ms : null;

  const isCached = !!aiResponse?.debug?.cached;

  const apiErrorRaw = String(aiResponse?.debug?.api_error || "");
  const hasApi429Fallback =
    apiErrorRaw.includes("429") || apiErrorRaw.includes("Too Many Requests");

  const answerText = String(aiResponse?.answer || "");

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 flex items-center justify-center">
      <div className="w-full max-w-4xl px-6 py-10 space-y-8">
        <h1 className="text-3xl font-bold">
          Gestionale Azienda AI – Playground (Spike)
        </h1>

        {/* HEALTH */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-xl font-semibold">Health Check</h2>
            <span className="text-xs text-slate-300">
              <span className="font-mono">GET /api/v1/health</span>
            </span>
          </div>

          {loadingHealth && (
            <p className="text-slate-300 mt-3">Caricamento stato…</p>
          )}

          {errorHealth && (
            <p className="mt-3 text-sm text-red-400">Errore: {errorHealth}</p>
          )}

          {status && !errorHealth && (
            <pre className="mt-4 bg-slate-950/60 rounded-xl p-4 font-mono text-sm overflow-x-auto border border-slate-800">
              {JSON.stringify(status, null, 2)}
            </pre>
          )}
        </div>

        {/* AI PLAYGROUND */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-xl font-semibold">AI Playground</h2>
            <span className="text-xs text-slate-300">
              <span className="font-mono">POST /api/v1/ai/chat</span>
            </span>
          </div>

          <form onSubmit={runAi} className="mt-4 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs text-slate-300 mb-1">
                  tenant_id
                </label>
                <input
                  value={tenantId}
                  onChange={(e) => setTenantId(e.target.value)}
                  className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-3 py-2 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-300 mb-1">skill</label>
                <select
                  value={skill}
                  onChange={(e) => setSkill(e.target.value)}
                  className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-3 py-2 text-sm"
                >
                  <option value="demo_rag">demo_rag (retrieval + optional LLM)</option>
                  <option value="chat">chat (OpenAI reale se key presente)</option>
                  <option value="mock">mock (no-LLM)</option>
                </select>
              </div>

              <div className="flex items-end gap-3">
                <button
                  type="submit"
                  disabled={aiLoading || (isPotentiallyOpenAi && cooldownLeft > 0)}
                  className="w-full md:w-auto bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 disabled:hover:bg-indigo-600 rounded-xl px-4 py-2 text-sm font-semibold"
                >
                  {aiLoading
                    ? "Esecuzione…"
                    : isPotentiallyOpenAi && cooldownLeft > 0
                    ? `Attendi ${cooldownLeft}s`
                    : "Invia"}
                </button>

                {isPotentiallyOpenAi && cooldownLeft > 0 && (
                  <span className="text-xs text-slate-300">anti-429 attivo</span>
                )}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <label className="inline-flex items-center gap-2 text-xs text-slate-300">
                <input
                  type="checkbox"
                  checked={useCache}
                  onChange={(e) => setUseCache(e.target.checked)}
                  className="accent-indigo-500"
                />
                cache (utile per demo_rag)
              </label>

              <button
                type="button"
                onClick={clearCache}
                className="text-xs border border-slate-700 hover:border-slate-500 rounded-lg px-3 py-1"
              >
                Svuota cache
              </button>

              <span className="text-xs text-slate-400">
                Suggerimento: per <span className="font-mono">chat</span> lascia cache OFF, così vedi risposte nuove.
              </span>
            </div>

            <div>
              <label className="block text-xs text-slate-300 mb-1">
                messaggio utente (query)
              </label>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                rows={4}
                className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-3 py-2 text-sm"
                placeholder="Scrivi qui e premi Invia…"
              />
              <p className="mt-2 text-xs text-slate-400">
                Tip keywords: <span className="font-mono">spike</span>,{" "}
                <span className="font-mono">provider</span>,{" "}
                <span className="font-mono">api</span>,{" "}
                <span className="font-mono">prebuilt</span>,{" "}
                <span className="font-mono">custom</span>,{" "}
                <span className="font-mono">contract</span>.
              </p>
            </div>
          </form>

          {aiError && (
            <p className="mt-4 text-sm text-red-400">Errore AI: {aiError}</p>
          )}

          {aiResponse && !aiError && (
            <div className="mt-4 space-y-3">
              <div className="text-xs text-slate-300 flex flex-wrap gap-x-3 gap-y-1">
                <span>
                  provider: <span className="font-mono">{provider}</span>
                </span>

                {latencyMs != null && (
                  <span>
                    • latency_ms: <span className="font-mono">{latencyMs}</span>
                  </span>
                )}

                <span>
                  • cached: <span className="font-mono">{String(isCached)}</span>
                </span>

                {aiResponse?.debug?.model && (
                  <span>
                    • model:{" "}
                    <span className="font-mono">{aiResponse.debug.model}</span>
                  </span>
                )}

                {hasApi429Fallback && (
                  <span className="text-amber-300">• fallback (rate limit)</span>
                )}
              </div>

              {hasApi429Fallback && (
                <div className="text-xs text-amber-200 bg-amber-900/20 border border-amber-700/40 rounded-xl p-3">
                  Nota: è scattato un rate limit (free tier). La risposta che vedi è un fallback (mock o demo_rag)
                  per mantenere la demo fluida.
                </div>
              )}

              {/* ANSWER (leggibile) */}
              <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800">
                <div className="text-xs text-slate-300 mb-2">Risposta</div>
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                  {answerText || "—"}
                </div>
              </div>

              {/* RAW JSON (debug) */}
              <details className="bg-slate-950/40 rounded-xl border border-slate-800">
                <summary className="cursor-pointer select-none px-4 py-3 text-xs text-slate-300">
                  Debug raw (JSON)
                </summary>
                <pre className="px-4 pb-4 font-mono text-sm overflow-x-auto">
                  {JSON.stringify(aiResponse, null, 2)}
                </pre>
              </details>
            </div>
          )}
        </div>

        {/* Payload preview */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-5">
          <div className="text-xs text-slate-300 mb-2">Payload corrente (debug)</div>
          <pre className="bg-slate-950/40 rounded-xl p-4 font-mono text-sm overflow-x-auto border border-slate-800">
            {JSON.stringify(payload, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}

export default App;
