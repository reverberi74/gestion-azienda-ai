# Gestionale Azienda AI – Casto Sistemi

Monorepo con tre componenti principali:

- **client/** → SPA React + Vite + Tailwind (frontend gestionale)
- **server/** → API Laravel 12 + MySQL (backend core)
- **service-ai/** → Microservizio AI in Python (FastAPI + Torch/Transformers)

Obiettivo: piattaforma gestionale AI-ready, riutilizzabile e verticalizzabile per diversi clienti (comuni, studi, aziende, ecc.).

---

## Struttura cartelle

```text
gestion-azienda-ai/
  ├─ client/      # React + Vite + Tailwind
  ├─ server/      # Laravel 12 + MySQL
  ├─ service-ai/  # FastAPI + AI engine (mock + provider futuri)
  └─ docs/        # Documentazione tecnica, ADR, note di progetto
Requisiti
PHP ≥ 8.2 + Composer

Node.js ≥ 20 + npm

Python 3.12 (per service-ai)

MySQL / MariaDB (DB: gestion_azienda_ai)

Setup rapido (dev)
1. Service AI

cd service-ai

# (se non esiste ancora il venv)
python -m venv .venv
source .venv/Scripts/activate  # su Git Bash/Windows

pip install -r requirements.txt

# avvio servizio AI (porta 8001)
./run_service_ai.sh
Health check:

GET http://127.0.0.1:8001/v1/health

GET http://127.0.0.1:8001/v1/ai/mock-chat (endpoint mock AI)

2. Laravel server

cd server

# .env già copiato da .env.example e DB configurato:
# DB_DATABASE=gestion_azienda_ai

php artisan migrate

# avvio API Laravel (porta 8000)
php artisan serve
Health check:

GET http://127.0.0.1:8000/api/v1/health

GET http://127.0.0.1:8000/api/health/ai (bridge verso service-ai)

3. React client

cd client

# (i node_modules sono già presenti,
# in caso reinstallare con:)
# npm install

npm run dev
Frontend dev:

http://localhost:5173

Mostra la pagina “Gestionale Azienda AI – Health Check” con il JSON di risposta di:

/api/v1/health (Laravel → service-ai).

Flussi di health-check
service-ai espone:

GET /v1/health

POST /v1/ai/mock-chat

server (Laravel) espone:

GET /api/v1/health → stato Laravel

GET /api/health/ai → chiama service-ai e ritorna stato AI

client (React):

chiama GET /api/v1/health

mostra il JSON in un pannello styled con Tailwind

Prossimi step (roadmap core)
R2: React Router (layout base, pagine stub)

R3: Redux Toolkit (auth, tenant, AI state)

L2: Auth Laravel (ruoli, token, multi-tenant)

AI-branch: primi provider reali (API esterna, modello preconfezionato, modello custom)
