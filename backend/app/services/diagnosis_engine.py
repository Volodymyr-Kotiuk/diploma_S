from statistics import mean

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models
from app.services.anomaly_detector import detect_anomaly
from app.utils.risk_utils import clamp, severity_from_risk, status_from_risk

DISK_RATE_HIGH = 50 * 1024 * 1024
NETWORK_RATE_HIGH = 50 * 1024 * 1024


def run_diagnostics_for_node(db: Session, node_id: int) -> models.Diagnostic:
    node = db.get(models.Node, node_id)
    metrics = list(
        reversed(
            db.scalars(
                select(models.ResourceMetric)
                .where(models.ResourceMetric.node_id == node_id)
                .order_by(desc(models.ResourceMetric.timestamp), desc(models.ResourceMetric.id))
                .limit(30)
            ).all()
        )
    )
    diagnostic_data = _diagnose(node, metrics, db)
    diagnostic = models.Diagnostic(node_id=node_id, **diagnostic_data)
    db.add(diagnostic)
    if node:
        node.status = status_from_risk(diagnostic_data["risk_score"])
    db.commit()
    db.refresh(diagnostic)

    if diagnostic.diagnosis_type == "healthy":
        from app.services.incident_service import resolve_open_incidents_for_node
        from app.services.recommendation_engine import resolve_active_recommendations_for_node

        resolve_open_incidents_for_node(db, node_id)
        resolve_active_recommendations_for_node(db, node_id)
    else:
        from app.services.incident_service import create_incident_from_diagnostic
        from app.services.recommendation_engine import create_recommendation_for_diagnostic

        create_incident_from_diagnostic(db, diagnostic)
        create_recommendation_for_diagnostic(db, diagnostic)
    return diagnostic


def _diagnose(node: models.Node | None, metrics: list[models.ResourceMetric], db: Session) -> dict:
    if not metrics:
        return _result("unknown_degradation", "Недостатньо даних", 10, 20, "Для вузла ще немає метрик ресурсів.", [])

    latest = metrics[-1]
    avg_cpu = _avg(metrics, "cpu_usage_percent")
    avg_ram = _avg(metrics, "ram_usage_percent")
    avg_swap = _avg(metrics, "swap_usage_percent")
    anomaly = detect_anomaly(metrics)
    evidence: list[dict] = []

    overcommit = _overcommit_evidence(node, db)
    if overcommit:
        evidence.extend(overcommit)
        return _result(
            "resource_overcommit",
            "Перевиділення ресурсів",
            82,
            88,
            "Сума виділених ресурсів перевищує доступні ліміти або ліміти конкретного вузла.",
            evidence,
            anomaly,
        )

    if (latest.temperature_celsius or 0) > 80:
        evidence.append(_ev("temperature_celsius", latest.temperature_celsius, "> 80", "Температура перевищує безпечний поріг."))
        return _result("thermal_risk", "Температурний ризик", clamp((latest.temperature_celsius or 80) + 5), 92, "Виявлено ризик перегріву або зниження продуктивності через температуру.", evidence, anomaly)

    if (latest.ram_usage_percent or 0) > 85 and (latest.swap_usage_percent or 0) > 20:
        evidence.extend(
            [
                _ev("ram_usage_percent", latest.ram_usage_percent, "> 85", "RAM майже вичерпана."),
                _ev("swap_usage_percent", latest.swap_usage_percent, "> 20", "Система активно використовує swap."),
            ]
        )
        return _result("swap_pressure", "Надмірне використання підкачки", max(latest.ram_usage_percent or 0, 78), 90, "Вузол компенсує нестачу RAM через підкачку, що збільшує затримки.", evidence, anomaly)

    if (latest.ram_usage_percent or 0) > 90 and (latest.ram_available_mb or 0) < max((latest.ram_total_mb or 4096) * 0.12, 512):
        evidence.extend(
            [
                _ev("ram_usage_percent", latest.ram_usage_percent, "> 90", "Використання RAM перевищує критичний поріг."),
                _ev("ram_available_mb", latest.ram_available_mb, "< 12% total або < 512 MB", "Доступної пам'яті замало для стабільної роботи."),
            ]
        )
        return _result("memory_pressure", "Нестача оперативної пам’яті", latest.ram_usage_percent or 85, 91, "Оперативної пам'яті недостатньо для поточного навантаження.", evidence, anomaly)

    if (latest.cpu_usage_percent or 0) > 85:
        evidence.extend(
            [
                _ev("cpu_usage_percent", latest.cpu_usage_percent, "> 85", "CPU використовується майже повністю."),
                _ev("load_average_1m", latest.load_average_1m, "інформаційно", "Середнє навантаження використовується як додатковий доказ, якщо доступне."),
            ]
        )
        return _result("cpu_saturation", "Перевантаження CPU", latest.cpu_usage_percent or 85, 92, "Процесорні ресурси є першопричиною деградації.", evidence, anomaly)

    disk_rate = max(latest.disk_read_rate or 0, latest.disk_write_rate or 0)
    if disk_rate > DISK_RATE_HIGH and (latest.cpu_usage_percent or 0) < 80:
        evidence.extend(
            [
                _ev("disk_read_rate", latest.disk_read_rate, f"> {DISK_RATE_HIGH}", "Висока швидкість читання з диска."),
                _ev("disk_write_rate", latest.disk_write_rate, f"> {DISK_RATE_HIGH}", "Висока швидкість запису на диск."),
                _ev("cpu_usage_percent", latest.cpu_usage_percent, "< 80", "CPU не є головним обмеженням."),
            ]
        )
        return _result("disk_io_bottleneck", "Обмеження дискових операцій", 76, 86, "Обмеження продуктивності спричинене дисковими операціями.", evidence, anomaly)

    net_rate = max(latest.network_sent_rate or 0, latest.network_recv_rate or 0)
    if net_rate > NETWORK_RATE_HIGH and (latest.cpu_usage_percent or 0) < 80 and (latest.ram_usage_percent or 0) < 85:
        evidence.extend(
            [
                _ev("network_sent_rate", latest.network_sent_rate, f"> {NETWORK_RATE_HIGH}", "Висока швидкість вихідного трафіку."),
                _ev("network_recv_rate", latest.network_recv_rate, f"> {NETWORK_RATE_HIGH}", "Висока швидкість вхідного трафіку."),
                _ev("cpu_usage_percent", latest.cpu_usage_percent, "< 80", "CPU не є першопричиною."),
            ]
        )
        return _result("network_pressure", "Навантаження мережі", 72, 84, "Основне навантаження припадає на пропускну здатність мережі.", evidence, anomaly)

    sustained_window = metrics[-8:] if len(metrics) >= 8 else metrics
    if _avg(sustained_window, "cpu_usage_percent") < 15 and _avg(sustained_window, "ram_usage_percent") < 30:
        evidence.extend(
            [
                _ev("cpu_usage_percent_avg", round(avg_cpu, 2), "< 15", "CPU тривалий час майже не використовується."),
                _ev("ram_usage_percent_avg", round(avg_ram, 2), "< 30", "Виділена RAM використовується частково."),
            ]
        )
        return _result("underutilization", "Недовикористання ресурсів", 28, 85, "Вузол має надлишково виділені ресурси.", evidence, anomaly)

    if (latest.service_latency_ms or 0) > 1000 or (latest.service_error_rate or 0) > 5:
        evidence.extend(
            [
                _ev("service_latency_ms", latest.service_latency_ms, "> 1000", "Сервіс відповідає повільно."),
                _ev("service_error_rate", latest.service_error_rate, "> 5", "Підвищена частка помилок."),
            ]
        )
        return _result("service_degradation", "Деградація сервісу", 68, 70, "Сервісні показники деградують, але ресурсна першопричина не підтверджена.", evidence, anomaly)

    if anomaly.get("is_anomaly") and anomaly.get("anomaly_score", 0) > 60:
        evidence.append(_ev("anomaly_score", anomaly["anomaly_score"], "> 60", anomaly.get("comment", "Виявлена аномалія.")))
        return _result("unknown_degradation", "Невизначена деградація", anomaly["anomaly_score"], 58, "Метрики виглядають нетипово, але конкретне обмеження не підтверджено.", evidence, anomaly)

    evidence.extend(
        [
            _ev("cpu_usage_percent", latest.cpu_usage_percent, "<= 85", "CPU у межах допустимого."),
            _ev("ram_usage_percent", latest.ram_usage_percent, "<= 90", "RAM у межах допустимого."),
            _ev("swap_pressure_condition", f"RAM {latest.ram_usage_percent}%, swap {latest.swap_usage_percent}%", "RAM > 85% і swap > 20%", "Swap pressure не підтверджено, бо умова RAM+swap не виконана."),
        ]
    )
    return _result("healthy", "Критичної деградації немає", 12, 78, "Критичних ознак деградації ресурсів не виявлено.", evidence, anomaly)


def _avg(metrics: list[models.ResourceMetric], attr: str) -> float:
    values = [float(getattr(metric, attr) or 0) for metric in metrics]
    return mean(values) if values else 0.0


def _ev(metric_name: str, current_value: object, threshold: object, explanation: str) -> dict:
    return {"metric": metric_name, "current_value": current_value, "threshold": threshold, "explanation": explanation}


def _result(dtype: str, root: str, risk: float, confidence: float, explanation: str, evidence: list[dict], anomaly: dict | None = None) -> dict:
    risk_score = clamp(float(risk))
    return {
        "diagnosis_type": dtype,
        "root_cause": root,
        "severity": severity_from_risk(risk_score),
        "confidence": clamp(confidence),
        "risk_score": risk_score,
        "explanation": f"{explanation} {anomaly.get('comment') if anomaly else ''}".strip(),
        "evidence_json": {"evidence": evidence, "anomaly": anomaly or {}},
        "status": "open",
    }


def _overcommit_evidence(node: models.Node | None, db: Session) -> list[dict]:
    if not node:
        return []
    evidence: list[dict] = []
    if node.allocated_cpu_cores and node.max_cpu_cores and node.allocated_cpu_cores > node.max_cpu_cores:
        evidence.append(_ev("allocated_cpu_cores", node.allocated_cpu_cores, f"<= {node.max_cpu_cores}", "Виділення CPU перевищує ліміт вузла."))
    if node.allocated_ram_mb and node.max_ram_mb and node.allocated_ram_mb > node.max_ram_mb:
        evidence.append(_ev("allocated_ram_mb", node.allocated_ram_mb, f"<= {node.max_ram_mb}", "Виділення RAM перевищує ліміт вузла."))
    if node.environment_id:
        nodes = db.scalars(select(models.Node).where(models.Node.environment_id == node.environment_id)).all()
        total_cpu = sum(n.allocated_cpu_cores or 0 for n in nodes)
        total_cpu_limit = sum(n.max_cpu_cores or n.allocated_cpu_cores or 0 for n in nodes)
        total_ram = sum(n.allocated_ram_mb or 0 for n in nodes)
        total_ram_limit = sum(n.max_ram_mb or n.allocated_ram_mb or 0 for n in nodes)
        if total_cpu_limit and total_cpu > total_cpu_limit:
            evidence.append(_ev("environment_allocated_cpu", total_cpu, f"<= {total_cpu_limit}", "Сумарне виділення CPU середовища перевищує доступний ліміт CPU."))
        if total_ram_limit and total_ram > total_ram_limit:
            evidence.append(_ev("environment_allocated_ram_mb", total_ram, f"<= {total_ram_limit}", "Сумарне виділення RAM середовища перевищує доступний ліміт RAM."))
    return evidence
