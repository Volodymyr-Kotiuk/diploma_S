# AutoInfraDiag Agent

Python agent збирає системні метрики через `psutil` і надсилає heartbeat та metrics у backend.

У вебінтерфейсі після створення Agent Node буде доступна команда запуску з правильним `node-id` і `token`.

## Запуск

```bash
pip install -r requirements.txt
python agent.py --server https://your-backend.onrender.com --node-id NODE_ID --token TOKEN --interval 5
```

Agent не виконує shell-команди, не зупиняє процеси і не змінює ресурси вузла. Він тільки надсилає метрики у backend.
