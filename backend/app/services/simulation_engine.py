from datetime import timedelta
from random import Random

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.services.diagnosis_engine import run_diagnostics_for_node
from app.utils.time_utils import utc_now

rng = Random(42)


def create_demo_environment(db: Session, name: str = "Демонстраційний віртуальний кластер") -> models.Environment:
    existing = db.scalar(select(models.Environment).where(models.Environment.name == name).limit(1))
    if existing:
        return existing
    env = models.Environment(name=name, description="Демонстраційний кластер для AutoInfraDiag.", environment_type="simulated", status="warning")
    db.add(env)
    db.commit()
    db.refresh(env)
    nodes = [
        ("Веб-вузол", "service", 2, 4096, 8, 16384, 80, "healthy"),
        ("API-вузол", "service", 2, 4096, 8, 16384, 80, "critical"),
        ("Вузол бази даних", "database", 4, 4096, 12, 32768, 160, "warning"),
        ("Фоновий вузол", "other", 4, 8192, 8, 16384, 80, "healthy"),
    ]
    created: dict[str, models.Node] = {}
    for node_name, role, cpu, ram, max_cpu, max_ram, disk_gb, status in nodes:
        node = models.Node(
            environment_id=env.id,
            name=node_name,
            description="Демонстраційний віртуальний вузол.",
            hostname=node_name.lower().replace(" ", "-"),
            node_type="virtual_node",
            role=role,
            status=status,
            os_name="Ubuntu",
            os_version="22.04 LTS",
            allocated_cpu_cores=cpu,
            allocated_ram_mb=ram,
            max_cpu_cores=max_cpu,
            max_ram_mb=max_ram,
            disk_total_gb=disk_gb,
        )
        db.add(node)
        db.commit()
        db.refresh(node)
        created[node_name] = node
    _generate_history(db, created["Веб-вузол"], "normal")
    _generate_history(db, created["API-вузол"], "cpu_saturation")
    _generate_history(db, created["Вузол бази даних"], "memory_pressure")
    _generate_history(db, created["Фоновий вузол"], "underutilization")
    for node in created.values():
        run_diagnostics_for_node(db, node.id)
    return env


def create_scenario(db: Session, payload: dict) -> models.SimulationScenario:
    env = db.get(models.Environment, payload["environment_id"])
    if not env:
        raise HTTPException(status_code=404, detail="Середовище не знайдено")
    scenario = models.SimulationScenario(**payload, status="created")
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


def run_scenario(db: Session, scenario_id: int) -> models.SimulationScenario:
    scenario = db.get(models.SimulationScenario, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Сценарій не знайдено")
    node = db.get(models.Node, scenario.target_node_id) if scenario.target_node_id else _first_env_node(db, scenario.environment_id)
    if not node:
        raise HTTPException(status_code=404, detail="Цільовий вузол не знайдено")
    scenario.status = "running"
    scenario.started_at = utc_now()
    db.commit()
    _generate_history(db, node, scenario.scenario_type, scenario.duration_seconds, scenario.intensity)
    run_diagnostics_for_node(db, node.id)
    scenario.status = "finished"
    scenario.finished_at = utc_now()
    db.commit()
    db.refresh(scenario)
    return scenario


def stop_scenario(db: Session, scenario_id: int) -> models.SimulationScenario:
    scenario = db.get(models.SimulationScenario, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Сценарій не знайдено")
    scenario.status = "stopped"
    scenario.finished_at = utc_now()
    db.commit()
    db.refresh(scenario)
    return scenario


def run_node_scenario(db: Session, node_id: int, scenario_type: str, duration_seconds: int = 300, intensity: float = 0.85) -> models.SimulationScenario:
    node = db.get(models.Node, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Вузол не знайдено")
    if node.node_type not in {"virtual_node", "simulated_vm"}:
        raise HTTPException(status_code=400, detail="Сценарій можна запускати тільки для віртуальних вузлів")
    if not node.environment_id:
        env = db.scalar(select(models.Environment).where(models.Environment.environment_type == "simulated").limit(1))
        if not env:
            env = models.Environment(name="Віртуальні вузли", description="Віртуальна інфраструктура для окремих вузлів.", environment_type="simulated", status="healthy")
            db.add(env)
            db.commit()
            db.refresh(env)
        node.environment_id = env.id
        db.commit()
    scenario = models.SimulationScenario(
        environment_id=node.environment_id,
        target_node_id=node.id,
        name=_scenario_label(scenario_type),
        scenario_type=scenario_type,
        duration_seconds=duration_seconds,
        intensity=intensity,
        status="running",
        started_at=utc_now(),
    )
    db.add(scenario)
    db.commit()
    _generate_history(db, node, scenario_type, duration_seconds, intensity)
    run_diagnostics_for_node(db, node.id)
    scenario.status = "finished"
    scenario.finished_at = utc_now()
    db.commit()
    db.refresh(scenario)
    return scenario


def _first_env_node(db: Session, environment_id: int) -> models.Node | None:
    return db.scalar(select(models.Node).where(models.Node.environment_id == environment_id).limit(1))


def _scenario_label(scenario_type: str) -> str:
    return {
        "cpu_saturation": "Перевантаження CPU",
        "memory_pressure": "Нестача пам’яті",
        "swap_pressure": "Навантаження підкачки",
        "disk_io_bottleneck": "Обмеження дискових операцій",
        "network_pressure": "Навантаження мережі",
        "resource_overcommit": "Перевиділення ресурсів",
        "underutilization": "Недовикористання ресурсів",
        "thermal_risk": "Температурний ризик",
        "mixed_resource_degradation": "Змішана деградація ресурсів",
    }.get(scenario_type, scenario_type)


def _generate_history(db: Session, node: models.Node, scenario_type: str, duration: int = 300, intensity: float = 0.85) -> None:
    points = max(12, min(120, duration // 5))
    base_time = utc_now() - timedelta(seconds=points * 5)
    disk_read_total = rng.randint(1_000_000_000, 8_000_000_000)
    disk_write_total = rng.randint(1_000_000_000, 8_000_000_000)
    net_sent_total = rng.randint(500_000_000, 3_000_000_000)
    net_recv_total = rng.randint(500_000_000, 3_000_000_000)
    for i in range(points):
        t = base_time + timedelta(seconds=i * 5)
        progress = i / max(points - 1, 1)
        values = _scenario_values(scenario_type, progress, intensity, node)
        disk_read_total += values["disk_read_rate"] * 5
        disk_write_total += values["disk_write_rate"] * 5
        net_sent_total += values["network_sent_rate"] * 5
        net_recv_total += values["network_recv_rate"] * 5
        metric = models.ResourceMetric(
            node_id=node.id,
            timestamp=t,
            cpu_usage_percent=values["cpu"],
            cpu_core_count=node.allocated_cpu_cores or 2,
            load_average_1m=values["load"],
            load_average_5m=max(values["load"] * 0.92, 0.1),
            load_average_15m=max(values["load"] * 0.72, 0.1),
            ram_total_mb=node.allocated_ram_mb or 4096,
            ram_used_mb=(node.allocated_ram_mb or 4096) * values["ram"] / 100,
            ram_usage_percent=values["ram"],
            ram_available_mb=(node.allocated_ram_mb or 4096) * (100 - values["ram"]) / 100,
            swap_total_mb=2048,
            swap_used_mb=2048 * values["swap"] / 100,
            swap_usage_percent=values["swap"],
            disk_total_gb=node.disk_total_gb or 80,
            disk_used_gb=(node.disk_total_gb or 80) * values["disk_usage"] / 100,
            disk_usage_percent=values["disk_usage"],
            disk_read_bytes=float(disk_read_total),
            disk_write_bytes=float(disk_write_total),
            disk_read_rate=values["disk_read_rate"],
            disk_write_rate=values["disk_write_rate"],
            network_bytes_sent=float(net_sent_total),
            network_bytes_recv=float(net_recv_total),
            network_sent_rate=values["network_sent_rate"],
            network_recv_rate=values["network_recv_rate"],
            process_count=int(values["process_count"]),
            uptime_seconds=86_400 + i * 5,
            temperature_celsius=values["temperature"],
            service_latency_ms=values["latency"],
            service_error_rate=values["error_rate"],
            custom_json={"simulated": True, "scenario": scenario_type},
        )
        db.add(metric)
    node.status = "online"
    node.last_heartbeat_at = utc_now()
    db.commit()


def _scenario_values(scenario: str, progress: float, intensity: float, node: models.Node) -> dict:
    noise = lambda spread=3: rng.uniform(-spread, spread)
    high = 75 + 23 * intensity * max(progress, 0.25)
    normal_cpu = 28 + noise()
    normal_ram = 45 + noise()
    values = {
        "cpu": normal_cpu,
        "ram": normal_ram,
        "swap": 3 + noise(1),
        "disk_usage": 48 + noise(3),
        "disk_read_rate": 5 * 1024 * 1024 + rng.randint(0, 2_000_000),
        "disk_write_rate": 4 * 1024 * 1024 + rng.randint(0, 2_000_000),
        "network_sent_rate": 2 * 1024 * 1024 + rng.randint(0, 1_000_000),
        "network_recv_rate": 3 * 1024 * 1024 + rng.randint(0, 1_000_000),
        "temperature": 50 + noise(4),
        "process_count": 90 + rng.randint(-8, 12),
        "latency": 80 + noise(20),
        "error_rate": max(0, noise(0.3)),
    }
    if scenario == "cpu_saturation":
        values.update(cpu=min(98, high + noise(2)), ram=48 + noise(), latency=420 + progress * 300, error_rate=1 + progress * 2)
    elif scenario == "memory_pressure":
        ram = min(98, high + noise(2))
        values.update(cpu=42 + noise(), ram=ram, swap=max(15, (ram - 78) * 1.8), latency=350 + progress * 250)
    elif scenario == "swap_pressure":
        values.update(cpu=45 + noise(), ram=min(96, 86 + progress * 10 + noise(1)), swap=min(80, 25 + progress * 45 + noise(3)), latency=500 + progress * 500)
    elif scenario == "disk_io_bottleneck":
        values.update(cpu=48 + noise(), ram=55 + noise(), disk_read_rate=80 * 1024 * 1024 + rng.randint(0, 70_000_000), disk_write_rate=95 * 1024 * 1024 + rng.randint(0, 80_000_000), latency=600 + progress * 450)
    elif scenario == "network_pressure":
        values.update(cpu=38 + noise(), ram=50 + noise(), network_sent_rate=90 * 1024 * 1024 + rng.randint(0, 80_000_000), network_recv_rate=110 * 1024 * 1024 + rng.randint(0, 80_000_000), latency=400 + progress * 350)
    elif scenario == "resource_overcommit":
        node.allocated_cpu_cores = (node.max_cpu_cores or node.allocated_cpu_cores or 2) + 2
        node.allocated_ram_mb = (node.max_ram_mb or node.allocated_ram_mb or 4096) + 2048
        values.update(cpu=70 + noise(), ram=75 + noise(), latency=500 + progress * 400)
    elif scenario == "underutilization":
        values.update(cpu=7 + noise(2), ram=18 + noise(3), swap=0, latency=35 + noise(8), error_rate=0)
    elif scenario == "thermal_risk":
        values.update(cpu=72 + noise(), ram=54 + noise(), temperature=82 + progress * 12 + noise(1), latency=300 + progress * 350)
    elif scenario == "mixed_resource_degradation":
        values.update(cpu=min(96, high + noise(3)), ram=min(96, 82 + progress * 12 + noise(2)), swap=28 + progress * 28, disk_write_rate=70 * 1024 * 1024, latency=800 + progress * 500, error_rate=2 + progress * 3)
    for key in ("cpu", "ram", "swap", "disk_usage"):
        values[key] = round(max(0, min(100, values[key])), 2)
    values["load"] = round(max(values["cpu"] / 100 * (node.allocated_cpu_cores or 2) * (1.6 if values["cpu"] > 85 else 0.9), 0.05), 2)
    values["temperature"] = round(values["temperature"], 2)
    values["latency"] = round(max(values["latency"], 1), 2)
    values["error_rate"] = round(max(values["error_rate"], 0), 2)
    return values
