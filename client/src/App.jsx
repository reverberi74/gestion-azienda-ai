// client/src/App.jsx

import { useEffect, useMemo, useState } from "react";

function App() {
  // Health
  const [status, setStatus] = useState(null);
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [errorHealth, setErrorHealth] = useState(null);

  // AI Playground
  const [tenantId, setTenantId] = useState("playground");
  const [skill, setSkill] = useState("demo_rag");
  const [query, setQuery] = useState(
    "Spiegami le differenze tra API, prebuilt e custom e perché usare branch spike."
  );
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState(null);
  const [aiResponse, setAiResponse] = useState(null);

  const payload = useMemo(
    () => ({
      tenant_id: tenantId,
      skill,
      query,
      locale: "it-IT",
      metadata: {
        source: "ai-playground",
        options: { temperature: 0.2, max_tokens: 200 },
      },
    }),
    [tenantId, skill, query]
  );

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
        setErrorHealth(err.message || "Errore sconosciuto");
      } finally {
        setLoadingHealth(false);
      }
    }
    loadHealth();
  }, []);

  async function runAi(e) {
    e?.preventDefault?.();

    try {
      setAiLoading(true);
      setAiError(null);
      setAiResponse(null);

      const res = await fetch("/api/v1/ai/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => null);

      if (!res.ok) {
        const msg = data?.error?.message || `HTTP ${res.status}`;
        throw new Error(msg);
      }

      setAiResponse(data);
    } catch (err) {
      setAiError(err.message || "Errore sconosciuto");
    } finally {
      setAiLoading(false);
    }
  }

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
                <label className="block text-xs text-slate-300 mb-1">
                  skill
                </label>
                <select
                  value={skill}
                  onChange={(e) => setSkill(e.target.value)}
                  className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-3 py-2 text-sm"
                >
                  <option value="demo_rag">demo_rag (core, no-LLM)</option>
                  <option value="chat">chat (mock)</option>
                </select>
              </div>

              <div className="flex items-end">
                <button
                  type="submit"
                  disabled={aiLoading}
                  className="w-full md:w-auto bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 disabled:hover:bg-indigo-600 rounded-xl px-4 py-2 text-sm font-semibold"
                >
                  {aiLoading ? "Esecuzione…" : "Esegui"}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs text-slate-300 mb-1">query</label>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                rows={4}
                className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-3 py-2 text-sm"
              />
              <p className="mt-2 text-xs text-slate-400">
                Tip: prova query con parole chiave tipo{" "}
                <span className="font-mono">spike</span>,{" "}
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
              <div className="text-xs text-slate-300">
                provider:{" "}
                <span className="font-mono">{aiResponse?.provider}</span>{" "}
                {aiResponse?.debug?.latency_ms != null && (
                  <>
                    • latency_ms:{" "}
                    <span className="font-mono">
                      {aiResponse.debug.latency_ms}
                    </span>
                  </>
                )}
              </div>

              <pre className="bg-slate-950/60 rounded-xl p-4 font-mono text-sm overflow-x-auto border border-slate-800">
                {JSON.stringify(aiResponse, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Payload preview */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-5">
          <div className="text-xs text-slate-300 mb-2">
            Payload corrente (debug)
          </div>
          <pre className="bg-slate-950/40 rounded-xl p-4 font-mono text-sm overflow-x-auto border border-slate-800">
            {JSON.stringify(payload, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}

export default App;
