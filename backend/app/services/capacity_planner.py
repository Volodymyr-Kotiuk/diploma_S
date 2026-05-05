from datetime import timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models
from app.utils.time_utils import utc_now


TARGETS = {
    "cpu_usage_percent": 85,
    "ram_usage_percent": 85,
    "disk_usage_percent": 90,
}


def run_capacity_planning(db: Session, node_id: int) -> list[models.CapacityForecast]:
    metrics = list(
        reversed(
            db.scalars(
                select(models.ResourceMetric)
                .where(models.ResourceMetric.node_id == node_id)
                .order_by(desc(models.ResourceMetric.timestamp), desc(models.ResourceMetric.id))
                .limit(80)
            ).all()
        )
    )
    old = db.scalars(select(models.CapacityForecast).where(models.CapacityForecast.node_id == node_id)).all()
    for row in old:
        db.delete(row)
    forecasts = [_forecast_metric(node_id, metrics, name, threshold) for name, threshold in TARGETS.items()]
    if metrics and _avg(metrics[-10:], "cpu_usage_percent") < 15 and _avg(metrics[-10:], "ram_usage_percent") < 30:
        latest = metrics[-1]
        forecasts.append(
            models.CapacityForecast(
                node_id=node_id,
                metric_name="underutilization",
                current_value=max(latest.cpu_usage_percent or 0, latest.ram_usage_percent or 0),
                predicted_value=None,
                predicted_threshold_time=None,
                trend_direction="low_usage",
                recommendation="Вузол використовує дуже малу частку CPU/RAM. Рекомендовано розглянути downscale або consolidation.",
            )
        )
    for forecast in forecasts:
        db.add(forecast)
    db.commit()
    for forecast in forecasts:
        db.refresh(forecast)
    return forecasts


def _forecast_metric(node_id: int, metrics: list[models.ResourceMetric], metric_name: str, threshold: float) -> models.CapacityForecast:
    if len(metrics) < 2:
        return models.CapacityForecast(
            node_id=node_id,
            metric_name=metric_name,
            current_value=getattr(metrics[-1], metric_name, None) if metrics else None,
            predicted_value=None,
            predicted_threshold_time=None,
            trend_direction="insufficient_data",
            recommendation="Недостатньо метрик для capacity forecast.",
        )
    values = [float(getattr(metric, metric_name) or 0) for metric in metrics]
    current = values[-1]
    slope = (values[-1] - values[0]) / max(len(values) - 1, 1)
    predicted = max(0, min(100, current + slope * 12))
    if slope > 0.25:
        trend = "up"
    elif slope < -0.25:
        trend = "down"
    else:
        trend = "stable"

    threshold_time = None
    if slope > 0 and current < threshold:
        points_to_threshold = (threshold - current) / slope
        minutes = max(points_to_threshold * 5, 1)
        threshold_time = utc_now() + timedelta(minutes=minutes)
        recommendation = f"{_label(metric_name)} має висхідний тренд. Якщо тенденція збережеться, поріг {threshold}% може бути досягнутий приблизно через {round(minutes)} хвилин."
    elif current >= threshold:
        threshold_time = utc_now()
        recommendation = f"{_label(metric_name)} вже перевищує поріг {threshold}%. Потрібна діагностика та план масштабування."
    elif trend == "down":
        recommendation = f"{_label(metric_name)} має спадний тренд. Додаткове масштабування наразі не є пріоритетним."
    else:
        recommendation = f"{_label(metric_name)} стабільна. Продовжуйте збирати метрики для точнішого прогнозу."

    return models.CapacityForecast(
        node_id=node_id,
        metric_name=metric_name,
        current_value=round(current, 2),
        predicted_value=round(predicted, 2),
        predicted_threshold_time=threshold_time,
        trend_direction=trend,
        recommendation=recommendation,
    )


def _avg(metrics: list[models.ResourceMetric], attr: str) -> float:
    if not metrics:
        return 0.0
    return sum(float(getattr(metric, attr) or 0) for metric in metrics) / len(metrics)


def _label(metric_name: str) -> str:
    return {
        "cpu_usage_percent": "CPU usage",
        "ram_usage_percent": "RAM usage",
        "disk_usage_percent": "Disk usage",
    }.get(metric_name, metric_name)
