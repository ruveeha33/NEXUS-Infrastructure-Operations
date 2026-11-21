"""Evidence-based infrastructure engineering reports."""

import os
import json
import stat
import hashlib
import subprocess
import tempfile

from pathlib import Path
from datetime import datetime

import psutil

from nexus_ui.services.telemetry import http_health
from nexus_ui.services.pipeline import pipeline_snapshot


ROOT = Path(__file__).resolve().parents[2]

REPORTS = ROOT / "evidence" / "reports"


def execute_check(action):

    try:

        result = subprocess.run(
            ["bash", "scripts/ops.sh", action],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

        return {
            "passed": result.returncode == 0,
            "returncode": result.returncode,
            "output": result.stdout[-30000:],
            "error": result.stderr[-5000:],
        }

    except (
        OSError,
        subprocess.TimeoutExpired,
    ) as exc:

        return {
            "passed": False,
            "returncode": None,
            "output": "",
            "error": type(exc).__name__,
        }


def system_snapshot():

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(str(ROOT))

    return {
        "cpu_percent": psutil.cpu_percent(
            interval=0.3
        ),
        "cpu_cores": psutil.cpu_count(),
        "memory_percent": memory.percent,
        "memory_used_gib": round(
            memory.used / 1024**3, 2
        ),
        "memory_total_gib": round(
            memory.total / 1024**3, 2
        ),
        "disk_percent": disk.percent,
        "process_count": len(psutil.pids()),
    }


def incident_summary(directory=None):

    directory = Path(
        directory or ROOT / "evidence" / "incidents"
    )

    records = []
    invalid = 0

    if directory.exists():

        for path in sorted(directory.glob("*.json")):

            try:

                if path.is_symlink():
                    raise ValueError("Symlink rejected")

                if not stat.S_ISREG(
                    path.stat().st_mode
                ):
                    raise ValueError("Invalid evidence")

                if path.stat().st_size > 2_000_000:
                    raise ValueError("Oversized evidence")

                data = json.loads(
                    path.read_text()
                )

                if not isinstance(data, dict):
                    raise ValueError("Invalid record")

                if not isinstance(
                    data.get("scenario"), str
                ):
                    raise ValueError("Invalid scenario")

                if type(data.get("detected")) is not bool:
                    raise ValueError("Invalid detection result")

                if type(data.get("recovered")) is not bool:
                    raise ValueError("Invalid recovery result")

                records.append({
                    "scenario": data["scenario"],
                    "detected": data["detected"],
                    "recovered": data["recovered"],
                    "root_cause": data.get("root_cause", ""),
                    "timestamp": data.get("timestamp", ""),
                })

            except (
                OSError,
                ValueError,
                TypeError,
            ):
                invalid += 1

    recovered = sum(
        r["detected"] and r["recovered"]
        for r in records
    )

    return {
        "total": len(records),
        "detected": sum(
            r["detected"] for r in records
        ),
        "recovered": recovered,
        "invalid_records": invalid,
        "recovery_rate": (
            round(
                recovered / len(records) * 100,
                2,
            )
            if records
            else None
        ),
        "scenarios": sorted({
            r["scenario"] for r in records
        }),
        "records": records,
    }


def checksum(path):

    h = hashlib.sha256()

    with path.open("rb") as file:

        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            h.update(block)

    return h.hexdigest()


def backup_summary():

    backups = []

    directory = ROOT / "backups"

    if directory.exists():

        for path in directory.rglob("*.tar.gz"):

            try:

                if path.is_symlink():
                    continue

                if not path.resolve().is_relative_to(
                    directory.resolve()
                ):
                    continue

                if not stat.S_ISREG(
                    path.stat().st_mode
                ):
                    continue

                backups.append({
                    "file": str(
                        path.relative_to(ROOT)
                    ),
                    "bytes": path.stat().st_size,
                    "modified": path.stat().st_mtime,
                })

            except OSError:
                continue

    backups.sort(
        key=lambda item: item["modified"],
        reverse=True,
    )

    latest = backups[0] if backups else None

    if latest:

        latest = dict(latest)

        latest["sha256"] = checksum(
            ROOT / latest["file"]
        )

    return {
        "archive_count": len(backups),
        "latest": latest,
    }


def release_assessment(
    health,
    security,
    acceptance,
    pipeline,
):

    operational = bool(
        health.get("online")
        and security["passed"]
        and acceptance["passed"]
    )

    if not operational:

        return {
            "local_status": "REVIEW REQUIRED",
            "release_status": "NOT READY",
            "reason": "Local operational checks failed",
        }

    if not pipeline.get("available"):

        return {
            "local_status": "PASSED",
            "release_status": "NOT VERIFIED",
            "reason": "Remote CI data unavailable",
        }

    if pipeline["local"]["dirty"]:

        return {
            "local_status": "PASSED",
            "release_status": "DEVELOPMENT",
            "reason": "Uncommitted working tree changes",
        }

    if not pipeline["summary"]["exact_commit_success"]:

        return {
            "local_status": "PASSED",
            "release_status": "NOT VERIFIED",
            "reason": "No successful matching-commit run",
        }

    return {
        "local_status": "PASSED",
        "release_status": "CI MATCH FOUND",
        "reason": (
            "Historical matching-commit CI found; "
            "final release approval remains separate"
        ),
    }


def markdown_report(data):

    system = data["system"]
    health = data["application"]
    incidents = data["incidents"]
    backups = data["backups"]
    pipeline = data["pipeline"]
    release = data["release"]

    lines = [
        "# NEXUS",
        "## Infrastructure Engineering Report",
        "",
        "**DECODELABS / DEVOPS PROJECT 01**",
        "",
        f"Generated: {data['timestamp']}",
        "",
        "## Executive Assessment",
        "",
        f"- Local verification: {release['local_status']}",
        f"- Release status: {release['release_status']}",
        f"- Reason: {release['reason']}",
        "",
        "## System Infrastructure",
        "",
        f"- CPU utilization: {system['cpu_percent']}%",
        f"- CPU cores: {system['cpu_cores']}",
        f"- Memory utilization: {system['memory_percent']}%",
        f"- Disk utilization: {system['disk_percent']}%",
        f"- Process count: {system['process_count']}",
        "",
        "## Application Availability",
        "",
        f"- Online: {health.get('online')}",
        f"- HTTP status: {health.get('status')}",
        "",
        "## Security and Acceptance",
        "",
        f"- Security audit passed: {data['security']['passed']}",
        f"- Acceptance passed: {data['acceptance']['passed']}",
        "",
        "## Backup Inventory",
        "",
        f"- Archives: {backups['archive_count']}",
    ]

    if backups["latest"]:

        lines.extend([
            f"- Latest: {backups['latest']['file']}",
            f"- SHA-256: {backups['latest']['sha256']}",
            "- Recovery verification is covered by acceptance tests.",
        ])

    lines.extend([
        "",
        "## Recorded Incident Response",
        "",
        f"- Recorded attempts: {incidents['total']}",
        f"- Detected: {incidents['detected']}",
        f"- Recovered: {incidents['recovered']}",
        f"- Recovery rate: {incidents['recovery_rate']}",
        f"- Invalid evidence records: {incidents['invalid_records']}",
        "",
        "Training incidents are not production outages.",
        "",
        "## GitHub Actions Intelligence",
        "",
        f"- Available: {pipeline.get('available')}",
    ])

    if pipeline.get("available"):

        summary = pipeline["summary"]
        local = pipeline["local"]

        lines.extend([
            f"- Repository: {local['repository']}",
            f"- Branch: {local['branch']}",
            f"- Commit: {local['commit']}",
            f"- Dirty working tree: {local['dirty']}",
            f"- Retrieved runs: {summary['total']}",
            f"- Successful runs: {summary['successful']}",
            f"- Failed runs: {summary['failed']}",
            f"- Recent success rate: {summary['success_rate']}",
            f"- Exact commit success: {summary['exact_commit_success']}",
        ])

    lines.extend([
        "",
        "## Raw Security Evidence",
        "",
        "~~~text",
        data["security"]["output"],
        "~~~",
        "",
        "## Raw Acceptance Evidence",
        "",
        "~~~text",
        data["acceptance"]["output"],
        "~~~",
        "",
        "---",
        "NEXUS Infrastructure Operations Workstation",
        "Local engineering evidence. Review before publication.",
    ])

    return "\n".join(lines) + "\n"


def generate_report(emit=print, destination=REPORTS):

    emit("[COLLECT] System infrastructure")

    system = system_snapshot()

    emit("[COLLECT] Application availability")

    health = http_health()

    emit("[CHECK] Execute security audit")

    security = execute_check("audit")

    emit("[CHECK] Execute acceptance tests")

    acceptance = execute_check("verify")

    emit("[COLLECT] Backup inventory")

    backups = backup_summary()

    emit("[COLLECT] Incident evidence")

    incidents = incident_summary()

    emit("[COLLECT] GitHub Actions intelligence")

    try:
        pipeline = pipeline_snapshot()

    except Exception as exc:

        pipeline = {
            "available": False,
            "error": type(exc).__name__,
        }

    # Avoid persisting remote credentials or raw CLI errors.
    if "local" in pipeline:
        pipeline["local"].pop("remote", None)

    pipeline.pop("error", None)
    pipeline.pop("remote_error", None)

    release = release_assessment(
        health,
        security,
        acceptance,
        pipeline,
    )

    data = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "system": system,
        "application": health,
        "security": security,
        "acceptance": acceptance,
        "backups": backups,
        "incidents": incidents,
        "pipeline": pipeline,
        "release": release,
    }

    emit("[ASSESS] " + release["release_status"])

    destination = Path(destination)

    destination.mkdir(
        mode=0o700,
        parents=True,
        exist_ok=True,
    )

    folder = Path(
        tempfile.mkdtemp(
            prefix="engineering-",
            dir=destination,
        )
    )

    payloads = {
        "report.json": json.dumps(
            data,
            indent=2,
        ),
        "report.md": markdown_report(data),
    }

    for filename, content in payloads.items():

        path = folder / filename

        with path.open("x") as file:

            os.fchmod(file.fileno(), 0o600)

            file.write(content)

    manifest = folder / "SHA256SUMS"

    with manifest.open("x") as file:

        os.fchmod(file.fileno(), 0o600)

        for filename in payloads:

            file.write(
                f"{checksum(folder / filename)}"
                f"  {filename}\n"
            )

    emit(f"[EXPORT] {folder}")

    return {
        "directory": str(folder),
        "data": data,
    }
