# AutoInfraDiag Backend

FastAPI backend для діагностики віртуалізованих ресурсів, remote agent metrics, simulation, RCA, incidents, recommendations, capacity planning і reports.

## Локальний запуск

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Після старту backend створює SQLite таблиці та demo environment, якщо база порожня.

## PostgreSQL/Supabase

Встановіть `DATABASE_URL` на PostgreSQL connection string Supabase. Для Render Web Service зазвичай зручний Supabase session pooler, якщо direct IPv6 недоступний.

```bash
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/postgres
```

Перед production стартом застосуйте міграцію:

```bash
alembic upgrade head
```

## Health

```bash
curl http://localhost:8000/api/health
```
