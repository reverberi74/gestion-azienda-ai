// client/src/App.jsx
import { useEffect, useState } from "react";

function App() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadHealth() {
      try {
        setLoading(true);
        setError(null);

        const res = await fetch("/api/v1/health");
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }

        const data = await res.json();
        setStatus(data);
      } catch (err) {
        setError(err.message || "Errore sconosciuto");
      } finally {
        setLoading(false);
      }
    }

    loadHealth();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 flex items-center justify-center">
      <div className="w-full max-w-3xl px-6 py-10">
        <h1 className="text-3xl font-bold mb-6">
          Gestionale Azienda AI – Health Check
        </h1>

        {loading && (
          <p className="text-slate-300">Caricamento stato…</p>
        )}

        {error && (
          <p className="mt-4 text-sm text-red-400">
            Errore chiamando <span className="font-mono">/api/v1/health</span>:{" "}
            {error}
          </p>
        )}

        {status && !error && (
          <pre className="mt-4 bg-slate-900 rounded-xl p-4 font-mono text-sm overflow-x-auto border border-slate-800 shadow-lg">
            {JSON.stringify(status, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

export default App;
