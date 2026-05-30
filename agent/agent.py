import argparse
import json
import logging
import platform
import socket
import time
from pathlib import Path

import psutil
import requests


AGENT_VERSION = "1.0.0"
LOG = logging.getLogger("autoinfradiag-agent")


class MetricsCollector:
    def __init__(self) -> None:
        self.last_time = None
        self.last_disk = None
        self.last_net = None

    def collect(self, node_id: int, token: str) -> dict:
        now = time.time()
        cpu = psutil.cpu_percent(interval=0.2)
        ram = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disk = psutil.disk_usage(Path.home().anchor or "/")
        disk_io = psutil.disk_io_counters()
        net = psutil.net_io_counters()
        elapsed = max(now - self.last_time, 1) if self.last_time else 1

        disk_read_rate = disk_write_rate = network_sent_rate = network_recv_rate = 0.0
        if self.last_disk and disk_io:
            disk_read_rate = max((disk_io.read_bytes - self.last_disk.read_bytes) / elapsed, 0)
            disk_write_rate = max((disk_io.write_bytes - self.last_disk.write_bytes) / elapsed, 0)
        if self.last_net and net:
            network_sent_rate = max((net.bytes_sent - self.last_net.bytes_sent) / elapsed, 0)
            network_recv_rate = max((net.bytes_recv - self.last_net.bytes_recv) / elapsed, 0)

        self.last_time = now
        self.last_disk = disk_io
        self.last_net = net
        load1, load5, load15 = self._load_average()
        return {
            "node_id": node_id,
            "token": token,
            "cpu_usage_percent": round(cpu, 2),
            "cpu_core_count": psutil.cpu_count(logical=True) or 1,
            "load_average_1m": load1,
            "load_average_5m": load5,
            "load_average_15m": load15,
            "ram_total_mb": self._mb(ram.total),
            "ram_used_mb": self._mb(ram.used),
            "ram_usage_percent": round(ram.percent, 2),
            "ram_available_mb": self._mb(ram.available),
            "swap_total_mb": self._mb(swap.total),
            "swap_used_mb": self._mb(swap.used),
            "swap_usage_percent": round(swap.percent, 2),
            "disk_total_gb": self._gb(disk.total),
            "disk_used_gb": self._gb(disk.used),
            "disk_usage_percent": round(disk.percent, 2),
            "disk_read_bytes": float(disk_io.read_bytes) if disk_io else 0.0,
            "disk_write_bytes": float(disk_io.write_bytes) if disk_io else 0.0,
            "disk_read_rate": round(disk_read_rate, 2),
            "disk_write_rate": round(disk_write_rate, 2),
            "network_bytes_sent": float(net.bytes_sent) if net else 0.0,
            "network_bytes_recv": float(net.bytes_recv) if net else 0.0,
            "network_sent_rate": round(network_sent_rate, 2),
            "network_recv_rate": round(network_recv_rate, 2),
            "process_count": len(psutil.pids()),
            "uptime_seconds": round(now - psutil.boot_time(), 2),
            "temperature_celsius": self._temperature(),
            "custom_json": {"agent_version": AGENT_VERSION, "hostname": socket.gethostname()},
        }

    @staticmethod
    def _mb(value: int | float) -> float:
        return round(float(value) / 1024 / 1024, 2)

    @staticmethod
    def _gb(value: int | float) -> float:
        return round(float(value) / 1024 / 1024 / 1024, 2)

    @staticmethod
    def _load_average() -> tuple[float | None, float | None, float | None]:
        try:
            load = psutil.getloadavg()
            return round(load[0], 2), round(load[1], 2), round(load[2], 2)
        except (AttributeError, OSError):
            return None, None, None

    @staticmethod
    def _temperature() -> float | None:
        try:
            temps = psutil.sensors_temperatures(fahrenheit=False)
        except (AttributeError, OSError):
            return None
        readings = [entry.current for entries in temps.values() for entry in entries if entry.current is not None]
        return round(max(readings), 2) if readings else None


def post_json(session: requests.Session, url: str, payload: dict, retries: int = 3) -> bool:
    for attempt in range(1, retries + 1):
        try:
            response = session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except requests.RequestException as exc:
            wait = min(2**attempt, 20)
            LOG.warning("Request failed (%s/%s): %s; retry in %ss", attempt, retries, exc, wait)
            time.sleep(wait)
    return False


def load_config(path: str | None) -> dict:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AutoInfraDiag remote metrics agent")
    parser.add_argument("--config", help="Optional JSON config path")
    parser.add_argument("--server", help="Backend root URL, for example https://domain.com")
    parser.add_argument("--token", help="Agent token")
    parser.add_argument("--node-id", type=int, help="Node id")
    parser.add_argument("--interval", type=int, default=5, help="Metrics interval in seconds")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()
    config = load_config(args.config)
    for key in ("server", "token", "node_id", "interval", "log_level"):
        if getattr(args, key, None) is None and key in config:
            setattr(args, key, config[key])
    if not args.server or not args.token or not args.node_id:
        parser.error("--server, --token and --node-id are required")
    return args


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(message)s")
    server = args.server.rstrip("/")
    heartbeat_url = f"{server}/api/heartbeat"
    metrics_url = f"{server}/api/metrics"
    session = requests.Session()
    collector = MetricsCollector()
    LOG.info("Starting AutoInfraDiag agent for node_id=%s server=%s", args.node_id, server)
    while True:
        heartbeat = {
            "node_id": args.node_id,
            "token": args.token,
            "hostname": socket.gethostname(),
            "os_name": platform.system(),
            "os_version": platform.platform(),
            "agent_version": AGENT_VERSION,
        }
        post_json(session, heartbeat_url, heartbeat)
        payload = collector.collect(args.node_id, args.token)
        ok = post_json(session, metrics_url, payload)
        LOG.info("Metrics sent" if ok else "Metrics delivery failed after retries")
        time.sleep(max(args.interval, 1))


if __name__ == "__main__":
    main()
