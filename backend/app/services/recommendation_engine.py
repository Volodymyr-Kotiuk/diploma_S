from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models


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
            "description": "На вузлі виявлено стабільно високе використання CPU та підвищений load average. Це свідчить про нестачу процесорних ресурсів.",
            "recommended_cpu": rec_cpu,
            "recommended_ram": ram,
            "reason": "CPU є основним bottleneck, тому додаткові ядра або application instances мають зменшити чергу виконання.",
            "expected_effect": "Зниження CPU utilization, load average і затримок сервісів під піковим навантаженням.",
            "actions": [
                f"Збільшити CPU cores: {cpu} -> {rec_cpu}.",
                "Перевірити процеси з найбільшим CPU.",
                "Розглянути горизонтальне масштабування application instances.",
                "Перевірити політики балансування навантаження.",
            ],
        }

    if dtype == "memory_pressure":
        rec_ram = min(_double(ram, 4096), node.max_ram_mb if node and node.max_ram_mb else max(_double(ram, 4096), 8192))
        return {
            "type": "vertical_ram_scaling",
            "title": "Рекомендовано збільшити RAM ресурси",
            "description": "На вузлі недостатньо оперативної пам'яті, система працює близько до ліміту і може переходити до swap.",
            "recommended_cpu": cpu,
            "recommended_ram": rec_ram,
            "reason": "RAM usage перевищує безпечний поріг, а доступна пам'ять низька.",
            "expected_effect": "Менше swap activity, стабільніший response time і нижчий ризик OOM.",
            "actions": [
                f"Збільшити RAM: {round(ram / 1024, 1)} GB -> {round(rec_ram / 1024, 1)} GB.",
                "Перевірити memory leaks у сервісах.",
                "Зменшити залежність від swap.",
                "Оптимізувати процеси з найбільшим memory footprint.",
            ],
        }

    if dtype == "swap_pressure":
        rec_ram = min(_double(ram, 4096), node.max_ram_mb if node and node.max_ram_mb else max(_double(ram, 4096), 8192))
        return {
            "type": "vertical_ram_scaling",
            "title": "Рекомендовано збільшити RAM і зменшити swap pressure",
            "description": "Вузол активно використовує swap, що суттєво повільніше за RAM і може деградувати сервіси.",
            "recommended_cpu": cpu,
            "recommended_ram": rec_ram,
            "reason": "Високе використання RAM разом зі swap вказує на нестачу оперативної пам'яті.",
            "expected_effect": "Менше дискових звернень swap і стабільніша робота застосунків.",
            "actions": [
                f"Збільшити RAM: {round(ram / 1024, 1)} GB -> {round(rec_ram / 1024, 1)} GB.",
                "Знайти процеси, що активно використовують пам'ять.",
                "Перевірити memory leak.",
                "Не покладатися на swap як основний ресурс.",
            ],
        }

    if dtype == "disk_io_bottleneck":
        return {
            "type": "storage_optimization",
            "title": "Рекомендовано оптимізувати дискову підсистему",
            "description": "Деградація пов'язана з високою інтенсивністю disk I/O. CPU scaling у цьому випадку не є пріоритетним.",
            "recommended_cpu": cpu,
            "recommended_ram": ram,
            "reason": "CPU/RAM не є критичними, bottleneck знаходиться у читанні або записі на диск.",
            "expected_effect": "Зменшення часу очікування I/O і стабілізація сервісів, що залежать від сховища.",
            "actions": [
                "Перевірити disk queues та latency.",
                "Оптимізувати запити БД або інтенсивні файлові операції.",
                "Використати SSD/NVMe або швидший storage tier.",
                "Додати кешування для гарячих даних.",
            ],
        }

    if dtype == "network_pressure":
        return {
            "type": "network_optimization",
            "title": "Рекомендовано оптимізувати мережевий шлях",
            "description": "Вузол має високу інтенсивність мережевого трафіку при нормальному CPU/RAM, тому вертикальне CPU/RAM scaling може бути неефективним.",
            "recommended_cpu": cpu,
            "recommended_ram": ram,
            "reason": "Основне обмеження пов'язане з throughput або балансуванням трафіку.",
            "expected_effect": "Менше мережевих черг, стабільніші відповіді сервісів і прогнозованіший трафік.",
            "actions": [
                "Перевірити bandwidth і мережеві ліміти провайдера.",
                "Перевірити балансувальник навантаження.",
                "Оптимізувати обсяг трафіку між сервісами.",
                "Розглядати горизонтальне масштабування лише якщо bottleneck на рівні application.",
            ],
        }

    if dtype == "thermal_risk":
        return {
            "type": "thermal_optimization",
            "title": "Рекомендовано усунути thermal risk",
            "description": "Температура вузла перевищує безпечний поріг. Збільшення CPU/RAM не вирішить першопричину.",
            "recommended_cpu": cpu,
            "recommended_ram": ram,
            "reason": "Ризик пов'язаний із перегрівом або throttling.",
            "expected_effect": "Зменшення thermal throttling і ризику аварійного вимкнення.",
            "actions": [
                "Перевірити охолодження.",
                "Очистити систему охолодження.",
                "Тимчасово зменшити навантаження.",
                "Перевірити hardware sensors і журнали вузла.",
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
            "reason": "Низьке sustained utilization свідчить про надлишкове виділення ресурсів.",
            "expected_effect": "Оптимізація витрат і вивільнення ресурсів для інших workload.",
            "actions": [
                f"Зменшити CPU allocation: {cpu} -> {rec_cpu}.",
                f"Зменшити RAM allocation: {round(ram / 1024, 1)} GB -> {round(rec_ram / 1024, 1)} GB.",
                "Об'єднати workload з іншими малонавантаженими вузлами.",
                "Після downscale контролювати latency і error rate.",
            ],
        }

    if dtype == "resource_overcommit":
        return {
            "type": "overcommit_optimization",
            "title": "Рекомендовано зменшити overcommit ресурсів",
            "description": "Віртуальним вузлам виділено більше CPU/RAM, ніж реально доступно у межах заданих лімітів.",
            "recommended_cpu": cpu,
            "recommended_ram": ram,
            "reason": "Overcommit може призвести до нестабільної продуктивності при одночасному піковому навантаженні.",
            "expected_effect": "Менший ризик contention між VM і прогнозованіша продуктивність.",
            "actions": [
                "Зменшити overcommit ratio.",
                "Перенести VM на інший host.",
                "Додати host resources.",
                "Переглянути CPU/RAM quotas для віртуальних вузлів.",
            ],
        }

    return {
        "type": "no_scaling_recommended",
        "title": "Масштабування наразі не рекомендоване",
        "description": "Система не має достатньо доказів, що CPU/RAM scaling вирішить проблему.",
        "recommended_cpu": cpu,
        "recommended_ram": ram,
        "reason": "Першопричина не підтверджена або метрик недостатньо.",
        "expected_effect": "Уникнення необґрунтованих змін ресурсів.",
        "actions": [
            "Зібрати більше метрик за довший період.",
            "Перевірити журнали сервісів.",
            "Повторити diagnostics після накопичення history.",
        ],
    }


def _apply_role_context(spec: dict, node: models.Node | None) -> None:
    role = (node.role if node else None) or "unknown"
    actions = spec.setdefault("actions", [])
    if role == "database":
        actions.append("Для database-вузла перевірити disk latency, кешування запитів і розмір buffer/cache.")
    elif role == "service":
        actions.append("Для service-вузла перевірити можливість горизонтального масштабування екземплярів сервісу.")
