# AutoInfraDiag Frontend

SvelteKit + TypeScript + Tailwind CSS frontend.

## Vercel

Для деплою з GitHub у Vercel:

- Root Directory: `frontend`
- Install Command: `npm install`
- Build Command: `npm run build`
- Output Directory: `build`

Environment Variable у Vercel:

```text
VITE_API_BASE_URL=https://your-backend.onrender.com/api
```

## Локальний запуск без env-файла

```bash
npm install
VITE_API_BASE_URL=http://localhost:8000/api npm run dev
```
