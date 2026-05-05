# AutoInfraDiag Backend

FastAPI backend для збору метрик, діагностики, рекомендацій, звітів і підключення agent.

## Render

Для деплою з GitHub:

- Environment: Docker
- Root Directory: `backend`
- Health Check Path: `/api/health`

Environment Variables задаються у Render UI:

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/postgres
ENVIRONMENT=production
API_PREFIX=/api
APP_NAME=AutoInfraDiag
BACKEND_CORS_ORIGINS=https://your-frontend.vercel.app
PUBLIC_BACKEND_URL=https://your-backend.onrender.com
SECRET_KEY=replace-with-long-random-secret
REPORTS_DIR=reports
```

## Локальний запуск без env-файла

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
DATABASE_URL=sqlite:///./autoinfradiag.db ENVIRONMENT=development BACKEND_CORS_ORIGINS=http://localhost:5173 uvicorn app.main:app --reload
```

Health endpoint:

```text
http://localhost:8000/api/health
```
