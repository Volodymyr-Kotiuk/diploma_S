# AutoInfraDiag

AutoInfraDiag — дипломний full-stack проєкт для діагностики та рекомендацій масштабування віртуалізованих обчислювальних ресурсів.

## Що реалізовано

- FastAPI backend з SQLAlchemy 2, SQLite локально і PostgreSQL/Supabase через `DATABASE_URL`.
- Node-centric модель: Agent Node для реального ПК/сервера і Virtual Node для змодельованого ресурсу.
- Python agent з `psutil`, heartbeat, metrics, retry і token auth.
- Virtual node сценарії для CPU overload, memory pressure, disk bottleneck, network pressure і underutilization.
- Diagnosis engine з root cause analysis, severity, confidence, risk score і evidence JSON.
- Recommendation engine українською мовою з action steps.
- Incident log, capacity planner, HTML reports, CSV/JSON export.
- SvelteKit + TypeScript + Tailwind CSS frontend українською мовою з ECharts-графіками.

## Backend локально

```bash
cd autoinfradiag/backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

API: `http://localhost:8000/api`

## Frontend локально

```bash
cd autoinfradiag/frontend
npm install
cp ../.env.example .env
npm run dev
```

UI: `http://localhost:5173`

## Remote agent

```bash
cd autoinfradiag/agent
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python agent.py --server http://localhost:8000 --node-id NODE_ID --token TOKEN --interval 5
```

Token і команду можна отримати на сторінці `/nodes/add` після вибору `Agent Node`.

## Supabase PostgreSQL

Створіть Supabase project, відкрийте Connect і скопіюйте PostgreSQL connection string. Для Render Web Service, якщо direct IPv6 недоступний, використовуйте Supabase session pooler. Встановіть:

```bash
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/postgres
BACKEND_CORS_ORIGINS=https://your-frontend-domain.com
```

Після встановлення `DATABASE_URL` застосуйте схему:

```bash
cd autoinfradiag/backend
alembic upgrade head
```

## Demo scenario

1. Запустіть backend і frontend.
2. Відкрийте `/dashboard`.
3. Demo data створюється автоматично, якщо база порожня.
4. Відкрийте `/nodes/add`, створіть `Virtual Node`.
5. Перейдіть у `/nodes/{id}`, натисніть “Запустити сценарій” і перевірте metrics, diagnosis, evidence, incidents та recommendations.

## Основні endpoints

- `GET /api/health`
- `GET /api/dashboard/summary`
- `GET|POST /api/nodes`
- `POST /api/heartbeat`
- `POST /api/metrics`
- `POST /api/agents/register`
- `POST /api/agents/heartbeat`
- `POST /api/agents/metrics`
- `POST /api/simulation/nodes/{node_id}/run`
- `POST /api/diagnostics/run/{node_id}`
- `GET /api/incidents`
- `GET /api/recommendations`
- `POST /api/reports/node/{node_id}`
- `GET /api/nodes/{id}/export/csv`
- `GET /api/nodes/{id}/export/json`

## Docker Compose

```bash
cd autoinfradiag
docker compose up --build
```

Frontend буде доступний на `http://localhost:3000`, backend на `http://localhost:8000`.
