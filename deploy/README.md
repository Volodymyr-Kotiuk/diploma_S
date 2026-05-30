# AutoInfraDiag Deploy

Ця папка містить тільки файли, потрібні для деплою:

- `render.yaml` - backend на Render.
- `vercel.json` - frontend на Vercel.

## Backend: Render

Рекомендовано створити Render Web Service з кореня репозиторію.

Параметри:

- Root Directory: `backend`
- Environment: `Docker`
- Health Check Path: `/api/health`

Якщо використовуєш Render Blueprint, файл `deploy/render.yaml` можна скопіювати в корінь репозиторію як `render.yaml`.

Environment Variables у Render:

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/postgres
ENVIRONMENT=production
API_PREFIX=/api
APP_NAME=AutoInfraDiag
BACKEND_CORS_ORIGINS=https://your-vercel-frontend.vercel.app
PUBLIC_BACKEND_URL=https://your-render-backend.onrender.com
SECRET_KEY=replace-with-long-random-secret
REPORTS_DIR=reports
```

`PUBLIC_BACKEND_URL` потрібен, щоб команда запуску agent автоматично містила Render URL, а не `localhost`.

## Frontend: Vercel

Рекомендовано створити Vercel Project з кореня репозиторію і вказати:

- Root Directory: `frontend`
- Framework Preset: `Other`
- Build Command: `npm run build`
- Output Directory: `build`
- Install Command: `npm install`

Якщо хочеш зберігати налаштування в репозиторії, файл `deploy/vercel.json` можна скопіювати у `frontend/vercel.json`.

Environment Variables у Vercel:

```text
VITE_API_BASE_URL=https://your-render-backend.onrender.com/api
```

## Порядок деплою

1. Створи базу PostgreSQL, наприклад Supabase.
2. Задеплой backend на Render.
3. У Render задай Environment Variables.
4. Після першого деплою скопіюй Render URL backend.
5. Додай цей URL у Render як `PUBLIC_BACKEND_URL`.
6. Створи frontend project на Vercel.
7. У Vercel задай `VITE_API_BASE_URL`.
8. У Render онови `BACKEND_CORS_ORIGINS` на Vercel URL frontend.
9. Redeploy backend і frontend.

## Перевірка

Backend:

```text
https://your-render-backend.onrender.com/api/health
```

Frontend:

```text
https://your-vercel-frontend.vercel.app
```

Після створення Agent Node команда має містити Render backend URL:

```text
python agent.py --server https://your-render-backend.onrender.com --node-id NODE_ID --token TOKEN --interval 5
```
