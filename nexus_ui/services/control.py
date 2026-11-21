from pathlib import Path
from datetime import datetime
import hashlib
import json
import os
import signal
import subprocess
import time
import fcntl

import psutil

from nexus_ui.services.telemetry import (
    ROOT,
    http_health,
)

PID_FILE = ROOT / "evidence/server.pid"
LOG_FILE = ROOT / "app/logs/server.log"
HISTORY = ROOT / "evidence/nexus-operations.jsonl"
LOCK_FILE = ROOT / "evidence/nexus-service.lock"

EXPECTED_ROOT = ROOT / "app/public"
PORT = 8095


def record(operation, success, detail):
    HISTORY.parent.mkdir(
        mode=0o700, exist_ok=True
    )

    event = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "operation": operation,
        "success": success,
        "detail": detail,
    }

    fd = os.open(
        HISTORY,
        os.O_WRONLY | os.O_CREAT | os.O_APPEND,
        0o600,
    )

    with os.fdopen(fd, "a") as handle:
        handle.write(json.dumps(event) + "\n")


def managed_process():
    try:
        pid = int(PID_FILE.read_text().strip())

        if pid <= 1:
            return None

        proc = psutil.Process(pid)

        if proc.uids().real != os.getuid():
            return None

        if Path(proc.cwd()).resolve() != ROOT:
            return None

        args = proc.cmdline()

        if len(args) < 4:
            return None

        if not Path(args[0]).name.startswith("python"):
            return None

        if "http.server" not in args:
            return None

        if str(PORT) not in args:
            return None

        if "--bind" not in args:
            return None

        if args[args.index("--bind") + 1] != "127.0.0.1":
            return None

        if "--directory" not in args:
            return None

        directory = args[
            args.index("--directory") + 1
        ]

        target = (ROOT / directory).resolve()

        if target != EXPECTED_ROOT.resolve():
            return None

        if proc.status() == psutil.STATUS_ZOMBIE:
            return None

        return proc

    except (
        OSError,
        ValueError,
        IndexError,
        psutil.Error,
    ):
        return None


def port_occupied():
    import socket

    with socket.socket(
        socket.AF_INET, socket.SOCK_STREAM
    ) as sock:
        sock.settimeout(0.5)

        return (
            sock.connect_ex(
                ("127.0.0.1", PORT)
            ) == 0
        )


def service_status():
    proc = managed_process()
    health = http_health()

    status = {
        "managed": proc is not None,
        "pid": None,
        "uptime": None,
        "memory_mib": None,
        "health": health,
    }

    if proc:
        try:
            status.update({
                "pid": proc.pid,
                "uptime": int(
                    time.time() - proc.create_time()
                ),
                "memory_mib": round(
                    proc.memory_info().rss / 1024**2,
                    2,
                ),
            })
        except psutil.Error:
            status["managed"] = False

    return status


def start_service():
    if managed_process():
        raise RuntimeError(
            "Managed application already running."
        )

    if port_occupied():
        raise RuntimeError(
            "Port 8095 is occupied. "
            "Refusing to interfere with another service."
        )

    PID_FILE.parent.mkdir(
        mode=0o700, exist_ok=True
    )

    with open(LOG_FILE, "ab") as log:
        proc = subprocess.Popen(
            [str(ROOT / "scripts/start.sh")],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )

    fd = os.open(
        PID_FILE,
        os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
        0o600,
    )

    with os.fdopen(fd, "w") as handle:
        handle.write(str(proc.pid) + "\n")

    for _ in range(30):
        if proc.poll() is not None:
            PID_FILE.unlink(missing_ok=True)

            raise RuntimeError(
                "Application startup failed. "
                "Inspect application logs."
            )

        if (
            managed_process()
            and http_health()["online"]
        ):
            return (
                f"Application started successfully. "
                f"PID: {proc.pid}"
            )

        time.sleep(0.2)

    # Clean up only the process launched by this attempt.
    # Never terminate an unrelated process occupying the port.
    if proc.poll() is None:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)

    PID_FILE.unlink(missing_ok=True)

    raise RuntimeError(
        "Startup did not pass health verification. "
        "Newly launched process cleaned up. "
        "Inspect service status and logs."
    )


def stop_service():
    proc = managed_process()

    if proc is None:
        raise RuntimeError(
            "No verified managed process. "
            "No process was terminated."
        )

    if not hasattr(os, "pidfd_open"):
        raise RuntimeError(
            "Safe Linux PID handles are unavailable."
        )

    pid = proc.pid
    handle = os.pidfd_open(pid)

    try:
        verified = managed_process()

        if (
            verified is None
            or verified.pid != pid
            or verified.create_time() != proc.create_time()
        ):
            raise RuntimeError(
                "Process identity changed."
            )

        signal.pidfd_send_signal(
            handle, signal.SIGTERM
        )

        try:
            proc.wait(timeout=8)
        except psutil.TimeoutExpired:
            raise RuntimeError(
                "Graceful shutdown timed out. "
                "No forced termination performed."
            )

    finally:
        os.close(handle)

    PID_FILE.unlink(missing_ok=True)

    if port_occupied():
        raise RuntimeError(
            "Managed process stopped, but port "
            "8095 remains occupied."
        )

    return f"Application stopped safely. PID: {pid}"


def restart_service():
    if managed_process():
        stop_service()

    return start_service()


def perform(operation):
    actions = {
        "start": start_service,
        "stop": stop_service,
        "restart": restart_service,
    }

    if operation not in actions:
        raise ValueError("Unsupported operation.")

    LOCK_FILE.parent.mkdir(
        mode=0o700, exist_ok=True
    )

    fd = os.open(
        LOCK_FILE,
        os.O_CREAT | os.O_RDWR,
        0o600,
    )

    with os.fdopen(fd, "a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)

        try:
            detail = actions[operation]()
            record(operation, True, detail)
            return True, detail

        except Exception as error:
            detail = str(error)
            record(operation, False, detail)
            return False, detail


def backup_inventory():
    rows = []

    for archive in sorted(
        (ROOT / "backups").rglob("*.tar.gz"),
        reverse=True,
    ):
        if archive.is_symlink():
            continue

        resolved = archive.resolve()

        if not resolved.is_relative_to(
            ROOT / "backups"
        ):
            continue

        digest = hashlib.sha256()

        with archive.open("rb") as handle:
            for chunk in iter(
                lambda: handle.read(1024 * 1024),
                b"",
            ):
                digest.update(chunk)

        rows.append((
            str(archive.relative_to(ROOT)),
            f"{archive.stat().st_size:,}",
            digest.hexdigest(),
        ))

    return rows


def operation_history():
    if not HISTORY.exists():
        return []

    events = []

    with HISTORY.open() as handle:
        for line in handle:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return events[-100:]
