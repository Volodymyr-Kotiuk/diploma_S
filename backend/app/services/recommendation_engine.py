from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models

ACTIVE_STATUSES = ("new", "accepted")

LEGACY_TEXT_REPLACEMENTS = {
    "використовує swap": "використовує підкачку",
    "зі swap": "з підкачкою",
    "до swap": "до підкачки",
    "звернень swap": "звернень підкачки",
    "на swap": "на підкачку",
    "swap як": "підкачку як",
    "swap pressure": "навантаження підкачки",
    "thermal risk": "температурний ризик",
    "thermal throttling": "температурного обмеження продуктивності",
    "throttling": "температурним зниженням продуктивності",
    "overcommit ресурсів": "перевиділення ресурсів",
    "Overcommit": "Перевиділення",
    "overcommit ratio": "коефіцієнт перевиділення",
    "CPU/RAM scaling": "збільшення CPU/RAM",
    "CPU scaling": "збільшення CPU",
    "CPU utilization": "використання CPU",
    "load average": "середнє навантаження",
    "CPU cores": "ядра CPU",
    "RAM usage": "використання RAM",
    "CPU allocation": "виділення CPU",
    "RAM allocation": "виділення RAM",
    "application instances": "екземпляри застосунку",
    "bottleneck": "обмеження",
    "throughput": "пропускною здатністю",
    "bandwidth": "пропускну здатність",
    "disk I/O": "дискових операцій",
    "disk queues": "черги диска",
    "disk latency": "затримку диска",
    "storage tier": "рівень сховища",
    "latency": "затримку",
    "memory leaks": "витоки пам’яті",
    "memory leak": "витоки пам’яті",
    "memory footprint": "споживанням пам’яті",
    "swap activity": "активності підкачки",
    "response time": "час відповіді",
    "OOM": "аварійного завершення через нестачу пам’яті",
    "hardware sensors": "апаратні датчики",
    "workload": "навантаження",
    "sustained utilization": "тривале низьке використання",
    "downscale": "зменшення ресурсів",
    "error rate": "частку помилок",
    "host resources": "ресурси хоста",
    "host": "хост",
    "CPU/RAM quotas": "квоти CPU/RAM",
    "quotas": "квоти",
    "contention": "конкуренції",
    "application": "застосунку",
    "database-вузла": "вузла бази даних",
    "service-вузла": "сервісного вузла",
    "Низьке тривале низьке використання": "Тривале низьке використання",
    "для інших навантаження": "для інших навантажень",
    "підвищений середнє навантаження": "підвищене середнє навантаження",
    "Зниження використання CPU, середнє навантаження": "Зниження використання CPU, середнього навантаження",
    "основним обмеження": "основним обмеженням",
    "масштабування екземпляри застосунку": "масштабування екземплярів застосунку",
    "Зменшення часу очікування I/O": "Зменшення часу очікування дискових операцій",
    "дискових операцій. збільшення": "дискових операцій. Збільшення",
}


def localize_legacy_recommendation(recommendation: models.Recommendation) -> models.Recommendation:
    for field in ("title", "description", "expected_effect", "reason"):
        value = getattr(recommendation, field, None)
        if isinstance(value, str):
            setattr(recommendation, field, _localize_text(value))

    actions = recommendation.action_steps_json
    if isinstance(actions, list):
        recommendation.action_steps_json = [_localize_text(action) if isinstance(action, str) else action for action in actions]
    return recommendation


def _localize_text(value: str) -> str:
    result = value
    for old, new in LEGACY_TEXT_REPLACEMENTS.items():
        result = result.replace(old, new)
    return result


def create_recommendation_for_diagnostic(db: Session, diagnostic: models.Diagnostic) -> models.Recommendation:
    node = db.get(models.Node, diagnostic.node_id)
    latest = db.scalar(
        select(models.ResourceMetric)
        .where(models.ResourceMetric.node_id == diagnostic.node_id)
        .order_by(desc(models.ResourceMetric.timestamp), desc(models.ResourceMetric.id))
        .limit(1)
    )
    current_cpu = node.allocated_cpu_cores if node else None
    current_ram = node.allocated_ram_mb if node else None
    spec = _recommendation_spec(diagnostic, node, latest)
    _apply_role_context(spec, node)

    existing = db.scalar(
        select(models.Recommendation)
        .where(
            models.Recommendation.node_id == diagnostic.node_id,
            models.Recommendation.status.in_(ACTIVE_STATUSES),
        )
        .order_by(desc(models.Recommendation.created_at), desc(models.Recommendation.id))
        .limit(1)
    )
    if existing:
        existing.diagnostic_id = diagnostic.id
        existing.recommendation_type = spec["type"]
        existing.title = spec["title"]
        existing.description = spec["description"]
        existing.priority = diagnostic.severity
        existing.current_cpu_cores = current_cpu
        existing.recommended_cpu_cores = spec.get("recommended_cpu")
        existing.current_ram_mb = current_ram
        existing.recommended_ram_mb = spec.get("recommended_ram")
        existing.expected_effect = spec["expected_effect"]
        existing.reason = spec["reason"]
        existing.action_steps_json = spec["actions"]
        existing.status = "new"
        _resolve_other_active_recommendations(db, diagnostic.node_id, existing.id)
        db.commit()
        db.refresh(existing)
        return existing

    recommendation = models.Recommendation(
        node_id=diagnostic.node_id,
        diagnostic_id=diagnostic.id,
        recommendation_type=spec["type"],
        title=spec["title"],
        description=spec["description"],
        priority=diagnostic.severity,
        current_cpu_cores=current_cpu,
        recommended_cpu_cores=spec.get("recommended_cpu"),
        current_ram_mb=current_ram,
        recommended_ram_mb=spec.get("recommended_ram"),
        expected_effect=spec["expected_effect"],
        reason=spec["reason"],
        action_steps_json=spec["actions"],
        status="new",
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    return recommendation


def resolve_active_recommendations_for_node(db: Session, node_id: int) -> int:
    rows = db.scalars(
        select(models.Recommendation).where(
            models.Recommendation.node_id == node_id,
            models.Recommendation.status.in_(ACTIVE_STATUSES),
        )
    ).all()
    for row in rows:
        row.status = "resolved"
    db.commit()
    return len(rows)


def _resolve_other_active_recommendations(db: Session, node_id: int, keep_id: int) -> None:
    rows = db.scalars(
        select(models.Recommendation).where(
            models.Recommendation.node_id == node_id,
            models.Recommendation.id != keep_id,
            models.Recommendation.status.in_(ACTIVE_STATUSES),
        )
    ).all()
    for row in rows:
        row.status = "resolved"


def _double(value: int | None, fallback: int) -> int:
    return max((value or fallback) * 2, fallback)


def _recommendation_spec(diagnostic: models.Diagnostic, node: models.Node | None, latest: models.ResourceMetric | None) -> dict:
    cpu = node.allocated_cpu_cores if node and node.allocated_cpu_cores else (latest.cpu_core_count if latest else 2)
    ram = node.allocated_ram_mb if node and node.allocated_ram_mb else (int(latest.ram_total_mb or 4096) if latest else 4096)
    dtype = diagnostic.diagnosis_type

    if dtype == "cpu_saturation":
        rec_cpu = min(_double(cpu, 2), node.max_cpu_cores if node and node.max_cpu_cores else max(_double(cpu, 2), 4))
        return {
            "type": "vertical_cpu_scaling",
            "title": "Рекомендовано збільшити CPU ресурси",
            "description": "На вузлі виявлено стабільно високе використання CPU та підвищене середнє навантаження. Це свідчить про нестачу процесорних ресурсів.",
            "recommended_cpu": rec_cpu,
            "recommended_ram": ram,
            "reason": "CPU є основним обмеженням, тому додаткові ядра або екземпляри застосунку мають зменшити чергу виконання.",
            "expected_effect": "Зниження використання CPU, середнього навантаження і затримок сервісів під піковим навантаженням.",
            "actions": [
                f"Збільшити ядра CPU: {cpu} -> {rec_cpu}.",
                "Перевірити процеси з найбільшим CPU.",
                "Розглянути горизонтальне масштабування екземплярів застосунку.",
                "Перевірити політики балансування навантаження.",
            ],
        }

    if dtype == "memory_pressure":
        rec_ram = min(_double(ram, 4096), node.max_ram_mb if node and node.max_ram_mb else max(_double(ram, 4096), 8192))
        return {
            "type": "vertical_ram_scaling",
            "title": "Рекомендовано збільшити RAM ресурси",
            "description": "На вузлі недостатньо оперативної пам'яті, система працює близько до ліміту і може переходити до підкачки.",
            "recommended_cpu": cpu,
            "recommended_ram": rec_ram,
            "reason": "Використання RAM перевищує безпечний поріг, а доступна пам'ять низька.",
            "expected_effect": "Менше активності підкачки, стабільніший час відповіді і нижчий ризик аварійного завершення через нестачу пам’яті.",
            "actions": [
                f"Збільшити RAM: {round(ram / 1024, 1)} GB -> {round(rec_ram / 1024, 1)} GB.",
                "Перевірити витоки пам’яті у сервісах.",
                "Зменшити залежність від підкачки.",
                "Оптимізувати процеси з найбільшим споживанням пам’яті.",
            ],
        }

    if dtype == "swap_pressure":
        rec_ram = min(_double(ram, 4096), node.max_ram_mb if node and node.max_ram_mb else max(_double(ram, 4096), 8192))
        return {
            "type": "vertical_ram_scaling",
            "title": "Рекомендовано збільшити RAM і зменшити навантаження підкачки",
            "description": "Вузол активно використовує підкачку, що суттєво повільніше за RAM і може деградувати сервіси.",
            "recommended_cpu": cpu,
            "recommended_ram": rec_ram,
            "reason": "Високе використання RAM разом зі swap вказує на нестачу оперативної пам'яті.",
            "expected_effect": "Менше дискових звернень підкачки і стабільніша робота застосунків.",
            "actions": [
                f"Збільшити RAM: {round(ram / 1024, 1)} GB -> {round(rec_ram / 1024, 1)} GB.",
                "Знайти процеси, що активно використовують пам'ять.",
                "Перевірити витоки пам’яті.",
                "Не покладатися на підкачку як основний ресурс.",
            ],
        }

    if dtype == "disk_io_bottleneck":
        return {
            "type": "storage_optimization",
            "title": "Рекомендовано оптимізувати дискову підсистему",
            "description": "Деградація пов'язана з високою інтенсивністю дискових операцій. Збільшення CPU у цьому випадку не є пріоритетним.",
            "recommended_cpu": cpu,
            "recommended_ram": ram,
            "reason": "CPU/RAM не є критичними, основне обмеження знаходиться у читанні або записі на диск.",
            "expected_effect": "Зменшення часу очікування дискових операцій і стабілізація сервісів, що залежать від сховища.",
            "actions": [
                "Перевірити черги диска та затримку операцій.",
                "Оптимізувати запити БД або інтенсивні файлові операції.",
                "Використати SSD/NVMe або швидший рівень сховища.",
                "Додати кешування для гарячих даних.",
            ],
        }

    if dtype == "network_pressure":
        return {
            "type": "network_optimization",
            "title": "Рекомендовано оптимізувати мережевий шлях",
            "description": "Вузол має високу інтенсивність мережевого трафіку при нормальному CPU/RAM, тому вертикальне збільшення CPU/RAM може бути неефективним.",
            "recommended_cpu": cpu,
            "recommended_ram": ram,
            "reason": "Основне обмеження пов'язане з пропускною здатністю або балансуванням трафіку.",
            "expected_effect": "Менше мережевих черг, стабільніші відповіді сервісів і прогнозованіший трафік.",
            "actions": [
                "Перевірити пропускну здатність і мережеві ліміти провайдера.",
                "Перевірити балансувальник навантаження.",
                "Оптимізувати обсяг трафіку між сервісами.",
                "Розглядати горизонтальне масштабування лише якщо обмеження знаходиться на рівні застосунку.",
            ],
        }

    if dtype == "thermal_risk":
        return {
            "type": "thermal_optimization",
            "title": "Рекомендовано усунути thermal risk",
            "description": "Температура вузла перевищує безпечний поріг. Збільшення CPU/RAM не вирішить першопричину.",
            "recommended_cpu": cpu,
            "recommended_ram": ram,
            "reason": "Ризик пов'язаний із перегрівом або температурним зниженням продуктивності.",
            "expected_effect": "Зменшення температурного обмеження продуктивності і ризику аварійного вимкнення.",
            "actions": [
                "Перевірити охолодження.",
                "Очистити систему охолодження.",
                "Тимчасово зменшити навантаження.",
                "Перевірити апаратні датчики і журнали вузла.",
            ],
        }

    if dtype == "underutilization":
        rec_cpu = max(1, int((cpu or 2) / 2))
        rec_ram = max(1024, int((ram or 4096) / 2))
        return {
            "type": "downscale",
            "title": "Рекомендовано зменшити виділені ресурси",
            "description": "Вузол тривалий час використовує малу частку CPU та RAM. Це створює резерв, який можна повернути кластеру.",
            "recommended_cpu": rec_cpu,
            "recommended_ram": rec_ram,
            "reason": "Тривале низьке використання свідчить про надлишкове виділення ресурсів.",
            "expected_effect": "Оптимізація витрат і вивільнення ресурсів для інших навантажень.",
            "actions": [
                f"Зменшити виділення CPU: {cpu} -> {rec_cpu}.",
                f"Зменшити виділення RAM: {round(ram / 1024, 1)} GB -> {round(rec_ram / 1024, 1)} GB.",
                "Об'єднати навантаження з іншими малонавантаженими вузлами.",
                "Після зменшення ресурсів контролювати затримку і частку помилок.",
            ],
        }

    if dtype == "resource_overcommit":
        return {
            "type": "overcommit_optimization",
            "title": "Рекомендовано зменшити перевиділення ресурсів",
            "description": "Віртуальним вузлам виділено більше CPU/RAM, ніж реально доступно у межах заданих лімітів.",
            "recommended_cpu": cpu,
            "recommended_ram": ram,
            "reason": "Перевиділення може призвести до нестабільної продуктивності при одночасному піковому навантаженні.",
            "expected_effect": "Менший ризик конкуренції між VM і прогнозованіша продуктивність.",
            "actions": [
                "Зменшити коефіцієнт перевиділення.",
                "Перенести VM на інший хост.",
                "Додати ресурси хоста.",
                "Переглянути квоти CPU/RAM для віртуальних вузлів.",
            ],
        }

    return {
        "type": "no_scaling_recommended",
        "title": "Масштабування наразі не рекомендоване",
        "description": "Система не має достатньо доказів, що збільшення CPU/RAM вирішить проблему.",
        "recommended_cpu": cpu,
        "recommended_ram": ram,
        "reason": "Першопричина не підтверджена або метрик недостатньо.",
        "expected_effect": "Уникнення необґрунтованих змін ресурсів.",
        "actions": [
            "Зібрати більше метрик за довший період.",
            "Перевірити журнали сервісів.",
            "Повторити діагностику після накопичення історії.",
        ],
    }


def _apply_role_context(spec: dict, node: models.Node | None) -> None:
    role = (node.role if node else None) or "unknown"
    actions = spec.setdefault("actions", [])
    if role == "database":
        actions.append("Для вузла бази даних перевірити затримку диска, кешування запитів і розмір буфера/кешу.")
    elif role == "service":
        actions.append("Для сервісного вузла перевірити можливість горизонтального масштабування екземплярів сервісу.")
