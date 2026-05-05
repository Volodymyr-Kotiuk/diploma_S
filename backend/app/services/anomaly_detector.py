from __future__ import annotations

import numpy as np

from app import models


FEATURES = [
    "cpu_usage_percent",
    "ram_usage_percent",
    "swap_usage_percent",
    "disk_usage_percent",
    "disk_read_rate",
    "disk_write_rate",
    "network_sent_rate",
    "network_recv_rate",
    "temperature_celsius",
]


def detect_anomaly(metrics: list[models.ResourceMetric]) -> dict:
    if len(metrics) < 12:
        return _rule_based(metrics)
    rows = []
    for metric in metrics:
        rows.append([float(getattr(metric, name) or 0) for name in FEATURES])
    data = np.asarray(rows, dtype=float)
    try:
        from sklearn.ensemble import IsolationForest

        model = IsolationForest(contamination=0.15, random_state=42)
        model.fit(data)
        scores = model.decision_function(data)
        latest_score = float(scores[-1])
        anomaly_score = round(max(0.0, min(100.0, (0.15 - latest_score) * 300)), 2)
        return {
            "mode": "isolation_forest",
            "is_anomaly": bool(model.predict(data[-1:])[0] == -1),
            "anomaly_score": anomaly_score,
            "comment": "IsolationForest позначив останній стан як нетиповий." if anomaly_score > 55 else "Суттєвої ML-аномалії не виявлено.",
        }
    except Exception:
        return _rule_based(metrics)


def _rule_based(metrics: list[models.ResourceMetric]) -> dict:
    latest = metrics[-1] if metrics else None
    if not latest:
        return {"mode": "rule_based", "is_anomaly": False, "anomaly_score": 0, "comment": "Немає достатньо метрик для аналізу."}
    score = max(
        latest.cpu_usage_percent or 0,
        latest.ram_usage_percent or 0,
        latest.swap_usage_percent or 0,
        latest.disk_usage_percent or 0,
        90 if (latest.temperature_celsius or 0) > 80 else 0,
    )
    return {
        "mode": "rule_based",
        "is_anomaly": score > 85,
        "anomaly_score": round(float(score), 2),
        "comment": "Використано rule-based fallback через малу кількість метрик.",
    }
