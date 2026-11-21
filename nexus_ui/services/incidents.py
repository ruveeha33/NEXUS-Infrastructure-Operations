"""Controlled infrastructure failure and recovery laboratory."""

import os
import json
import time
import stat
import hashlib
import shutil
import tempfile
import threading
import urllib.request

from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from http.server import (
    ThreadingHTTPServer,
    SimpleHTTPRequestHandler,
)
from functools import partial


ROOT = Path(__file__).resolve().parents[2]

EVIDENCE = ROOT / "evidence" / "incidents"

SCENARIOS = {
    "configuration": "Invalid application configuration",
    "permissions": "Incorrect configuration permissions",
    "missing_file": "Missing application deployment",
    "integrity": "Unexpected application modification",
    "outage": "HTTP service unavailable",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass
class IncidentResult:

    scenario: str
    title: str
    timestamp: str
    detected: bool
    recovered: bool
    root_cause: str
    duration_ms: float
    events: list


class SilentHandler(SimpleHTTPRequestHandler):

    def log_message(self, *args):
        pass


class TrainingService:

    def __init__(self, directory):
        self.directory = directory
        self.server = None
        self.thread = None
        self.port = None

    def start(self):

        if self.server is not None:
            raise RuntimeError("Service already running")

        handler = partial(
            SilentHandler,
            directory=str(self.directory),
        )

        self.server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            handler,
        )

        self.port = self.server.server_port

        self.thread = threading.Thread(
            target=self.server.serve_forever,
            kwargs={"poll_interval": 0.05},
            daemon=True,
        )

        self.thread.start()

    def stop(self):

        if self.server is None:
            return

        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

        self.server = None
        self.thread = None

    def healthy(self):

        if self.port is None:
            return False

        try:
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({})
            )

            with opener.open(
                f"http://127.0.0.1:{self.port}/",
                timeout=2,
            ) as response:

                return (
                    response.status == 200
                    and response.read()
                    == b"NEXUS INCIDENT LAB\n"
                )

        except (OSError, ValueError):
            return False


def config_valid(path):

    try:

        settings = dict(
            line.split("=", 1)
            for line in path.read_text().splitlines()
            if line
        )

        return (
            settings.get("APP_ENV") == "training"
            and settings.get("APP_HOST") == "127.0.0.1"
            and 1024 <= int(settings["APP_PORT"]) <= 65535
        )

    except (OSError, ValueError, KeyError):
        return False


def run_incident(
    scenario,
    emit=print,
    evidence_dir=EVIDENCE,
):

    if scenario not in SCENARIOS:
        raise ValueError("Unknown incident scenario")

    if os.getuid() == 0:
        raise RuntimeError("Run incident lab as regular user")

    started = time.perf_counter()

    events = []

    def event(stage, detail):

        entry = {
            "timestamp": datetime.now().astimezone().isoformat(),
            "stage": stage,
            "detail": detail,
        }

        events.append(entry)

        emit(f"[{stage.upper()}] {detail}")

    detected = False
    recovered = False
    cause = ""

    with tempfile.TemporaryDirectory(
        prefix="nexus-incident-"
    ) as directory:

        lab = Path(directory)

        app = lab / "public"
        app.mkdir(mode=0o700)

        config = lab / "config.conf"
        config.write_text(
            "APP_ENV=training\n"
            "APP_HOST=127.0.0.1\n"
            "APP_PORT=8095\n"
        )

        config.chmod(0o600)

        index = app / "index.html"
        index.write_bytes(b"NEXUS INCIDENT LAB\n")

        backup = lab / "index.html.bak"
        shutil.copy2(index, backup)

        expected_hash = digest(index)

        config_backup = lab / "config.bak"
        shutil.copy2(config, config_backup)

        config_hash = digest(config_backup)

        service = TrainingService(app)

        event(
            "baseline",
            "Temporary training environment created",
        )

        try:

            if scenario == "configuration":

                if not config_valid(config):
                    raise RuntimeError("Invalid baseline")

                config.write_text(
                    "APP_ENV=training\n"
                    "APP_HOST=127.0.0.1\n"
                    "APP_PORT=INVALID\n"
                )

                event(
                    "inject",
                    "Replaced valid port with invalid configuration",
                )

                detected = not config_valid(config)

                cause = "APP_PORT is not a valid numeric port"

                event("detect", str(detected))
                event("diagnose", cause)

                if digest(config_backup) != config_hash:
                    raise RuntimeError("Backup integrity failure")

                shutil.copy2(config_backup, config)

                event(
                    "recover",
                    "Restored verified configuration backup",
                )

                recovered = (
                    config_valid(config)
                    and digest(config) == config_hash
                )

            elif scenario == "permissions":

                if stat.S_IMODE(
                    config.stat().st_mode
                ) != 0o600:
                    raise RuntimeError("Invalid baseline permissions")

                config.chmod(0o644)

                event(
                    "inject",
                    "Configuration permissions changed to 644",
                )

                observed = stat.S_IMODE(
                    config.stat().st_mode
                )

                detected = observed != 0o600

                cause = (
                    f"Observed {observed:o}; "
                    "required 600"
                )

                event("detect", str(detected))
                event("diagnose", cause)

                config.chmod(0o600)

                event(
                    "recover",
                    "Restored least-privilege permissions",
                )

                recovered = (
                    stat.S_IMODE(config.stat().st_mode)
                    == 0o600
                )

            elif scenario == "missing_file":

                index.unlink()

                event(
                    "inject",
                    "Removed temporary deployment file",
                )

                detected = not index.exists()

                cause = "Required index.html is missing"

                event("detect", str(detected))
                event("diagnose", cause)

                if digest(backup) != expected_hash:
                    raise RuntimeError("Backup integrity failure")

                shutil.copy2(backup, index)

                event(
                    "recover",
                    "Recovered deployment from verified backup",
                )

                recovered = (
                    index.exists()
                    and digest(index) == expected_hash
                )

            elif scenario == "integrity":

                index.write_text(
                    "CONTROLLED INTEGRITY INCIDENT\n"
                )

                event(
                    "inject",
                    "Modified temporary application content",
                )

                observed_hash = digest(index)

                detected = observed_hash != expected_hash

                cause = "Application SHA-256 fingerprint mismatch"

                event("detect", str(detected))
                event("diagnose", cause)

                event(
                    "evidence",
                    f"Expected SHA-256: {expected_hash}",
                )

                event(
                    "evidence",
                    f"Observed SHA-256: {observed_hash}",
                )

                if digest(backup) != expected_hash:
                    raise RuntimeError("Backup integrity failure")

                shutil.copy2(backup, index)

                event(
                    "recover",
                    "Restored original application content",
                )

                recovered = digest(index) == expected_hash

            elif scenario == "outage":

                service.start()

                if not service.healthy():
                    raise RuntimeError("Baseline HTTP service failed")

                event(
                    "baseline",
                    f"Training HTTP service healthy on "
                    f"127.0.0.1:{service.port}",
                )

                service.stop()

                event(
                    "inject",
                    "Stopped temporary HTTP service",
                )

                detected = not service.healthy()

                cause = "Temporary HTTP listener unavailable"

                event("detect", str(detected))
                event("diagnose", cause)

                service.start()

                event(
                    "recover",
                    f"Temporary HTTP service restarted "
                    f"on port {service.port}",
                )

                recovered = service.healthy()

            event(
                "verify",
                "Recovery successful"
                if recovered
                else "Recovery failed",
            )

            if not detected or not recovered:
                raise RuntimeError(
                    "Incident response verification failed"
                )

        finally:
            service.stop()

    event(
        "cleanup",
        "Temporary training resources removed",
    )

    result = IncidentResult(
        scenario=scenario,
        title=SCENARIOS[scenario],
        timestamp=datetime.now().astimezone().isoformat(),
        detected=detected,
        recovered=recovered,
        root_cause=cause,
        duration_ms=round(
            (time.perf_counter() - started) * 1000,
            2,
        ),
        events=events,
    )

    evidence_dir = Path(evidence_dir)

    evidence_dir.mkdir(
        parents=True,
        exist_ok=True,
        mode=0o700,
    )

    with tempfile.NamedTemporaryFile(
        mode="w",
        prefix=f"{scenario}-",
        suffix=".json",
        dir=evidence_dir,
        delete=False,
    ) as report:

        json.dump(
            asdict(result),
            report,
            indent=2,
        )

    emit(f"[EVIDENCE] {report.name}")

    return result
