# AutoInfraDiag Remote Agent

Agent збирає системні метрики через `psutil` і надсилає heartbeat та metrics у backend AutoInfraDiag.

## Запуск

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python agent.py --server http://localhost:8000 --node-id NODE_ID --token TOKEN --interval 5
```

На Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python agent.py --server http://localhost:8000 --node-id NODE_ID --token TOKEN --interval 5
```

Agent не виконує shell-команди, не зупиняє процеси і не змінює ресурси вузла. Він тільки надсилає `POST /api/heartbeat` та `POST /api/metrics`.
