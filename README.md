# AutoInfraDiag

AutoInfraDiag - система діагностики обчислювальних вузлів і формування рекомендацій масштабування.

Ця папка підготовлена як окремий GitHub-ready репозиторій для деплою:

- backend: Render Web Service через Docker;
- frontend: Vercel Static/SvelteKit project;
- database: PostgreSQL, наприклад Supabase;
- env-файли не потрібні, змінні задаються у Render та Vercel Environment Variables.

## Структура

```text
backend/       FastAPI backend, Dockerfile, Alembic, SQLAlchemy
frontend/      SvelteKit frontend, Vercel config
agent/         Python agent для реального ПК/сервера
render.yaml    Render blueprint тільки для backend
.gitignore     виключає локальні env, БД, build, node_modules, reports
```

## 1. Завантаження на GitHub

1. Створи новий GitHub repository.
2. Завантаж у нього вміст цієї папки.
3. Не додавай локальні `.env`, `.db`, `node_modules`, `build`, `.svelte-kit`, `.venv`.

## 2. Backend на Render

Варіант A - через `render.yaml`:

1. У Render створи Blueprint.
2. Обери GitHub repository з цим проєктом.
3. Render прочитає `render.yaml`.
4. Після створення сервісу задай Environment Variables.

Варіант B - вручну:

- Service Type: Web Service
- Environment: Docker
- Root Directory: `backend`
- Health Check Path: `/api/health`

Environment Variables у Render:

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

`PUBLIC_BACKEND_URL` використовується для генерації команди запуску agent.

Перевірка backend:

```text
https://your-backend.onrender.com/api/health
```

## 3. Frontend на Vercel

1. У Vercel створи New Project.
2. Обери той самий GitHub repository.
3. Укажи Root Directory: `frontend`.
4. Vercel використає `frontend/vercel.json`.

Якщо налаштовуєш вручну:

- Framework Preset: Other
- Install Command: `npm install`
- Build Command: `npm run build`
- Output Directory: `build`

Environment Variables у Vercel:

```text
VITE_API_BASE_URL=https://your-backend.onrender.com/api
```

Після отримання Vercel URL онови на Render:

```text
BACKEND_CORS_ORIGINS=https://your-frontend.vercel.app
```

Після цього зроби Redeploy backend.

## 4. Agent Node

У вебінтерфейсі створи Agent Node. Система покаже:

```text
pip install psutil requests
python agent.py --server https://your-backend.onrender.com --node-id NODE_ID --token TOKEN --interval 5
```

Файл `agent.py` можна завантажити з вебінтерфейсу кнопкою `Завантажити agent.py`.

## 5. Virtual Node

У вебінтерфейсі створи Virtual Node і запусти сценарій навантаження на сторінці вузла. Метрики, діагностика, інциденти та рекомендації показуються тільки в контексті конкретного вузла.

## 6. Важливий порядок деплою

1. Створи PostgreSQL базу.
2. Задеплой backend на Render.
3. Задай Render Environment Variables.
4. Задеплой frontend на Vercel.
5. Задай `VITE_API_BASE_URL` у Vercel.
6. У Render задай `BACKEND_CORS_ORIGINS` як Vercel URL.
7. Перезапусти backend і frontend.
