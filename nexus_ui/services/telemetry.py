from pathlib import Path
from collections import Counter
from datetime import datetime
import platform
import re
import time
import urllib.request
import psutil

ROOT = Path(__file__).resolve().parents[2]
LOG_FILE = ROOT / "app/logs/server.log"
URL = "http://127.0.0.1:8095/?probe=nexus"

def snapshot():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(str(ROOT))

    return {
        "cpu": psutil.cpu_percent(interval=None),
        "cores": psutil.cpu_count() or 0,
        "memory": memory.percent,
        "memory_used": memory.used / 1024**3,
        "memory_total": memory.total / 1024**3,
        "disk": disk.percent,
        "disk_used": disk.used / 1024**3,
        "disk_total": disk.total / 1024**3,
        "processes": len(psutil.pids()),
        "uptime": int(time.time() - psutil.boot_time()),
        "kernel": platform.release(),
        "host": platform.node(),
        "time": datetime.now().strftime("%H:%M:%S"),
    }

def http_health():
    start = time.perf_counter()

    try:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({})
        )
        with opener.open(URL, timeout=1) as response:
            body = response.read(65536)
            return {
                "online": response.status == 200
                and b"Linux Operations Lab" in body,
                "status": response.status,
                "latency": round(
                    (time.perf_counter() - start) * 1000, 1
                ),
            }
    except Exception:
        return {
            "online": False,
            "status": None,
            "latency": None,
        }

def log_snapshot():
    if not LOG_FILE.exists():
        return Counter(), []

    try:
        with LOG_FILE.open("rb") as handle:
            handle.seek(0, 2)
            size = handle.tell()
            handle.seek(max(0, size - 262144))
            lines = handle.read().decode(
                "utf-8", errors="replace"
            ).splitlines()

        counts = Counter()

        for line in lines:
            match = re.search(
                r'"\s+([1-5][0-9]{2})\s+', line
            )
            if "probe=nexus" in line:
                counts["probe"] += 1
            elif match:
                counts[match.group(1)] += 1

        return counts, lines[-20:]

    except OSError:
        return Counter(), []

def process_snapshot():
    result = []

    for proc in psutil.process_iter(
        ["pid", "name", "memory_percent"]
    ):
        try:
            result.append(proc.info)
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):
            continue

    return sorted(
        result,
        key=lambda p: p.get("memory_percent") or 0,
        reverse=True,
    )[:12]
