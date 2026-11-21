"""Read-only GitHub Actions pipeline intelligence."""

import json
import subprocess

from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]

REPOSITORY = (
    "HaziqBinAfzal/"
    "DevOps-Project-01-Linux-Fundamentals"
)

FIELDS = ",".join([
    "databaseId",
    "displayTitle",
    "workflowName",
    "status",
    "conclusion",
    "createdAt",
    "startedAt",
    "updatedAt",
    "headBranch",
    "headSha",
    "event",
    "url",
])


def execute(args, timeout=20):

    result = subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
            or "Command execution failed"
        )

    return result.stdout.strip()


def git(*args):
    return execute(["git", *args])


def local_repository():

    return {
        "repository": REPOSITORY,
        "branch": git("branch", "--show-current"),
        "commit": git("rev-parse", "HEAD"),
        "message": git("log", "-1", "--format=%s"),
        "dirty": bool(
            git("status", "--porcelain")
        ),
        "remote": git("remote", "get-url", "origin"),
    }


def duration_seconds(run):

    if run.get("status") != "completed":
        return None

    try:
        started = datetime.fromisoformat(
            run["startedAt"].replace("Z", "+00:00")
        )

        finished = datetime.fromisoformat(
            run["updatedAt"].replace("Z", "+00:00")
        )

        elapsed = (
            finished - started
        ).total_seconds()

        return max(0, round(elapsed))

    except (KeyError, TypeError, ValueError):
        return None


def normalize_run(run):

    return {
        "id": run.get("databaseId"),
        "workflow": run.get("workflowName", "Unknown"),
        "title": run.get("displayTitle", ""),
        "status": run.get("status", "unknown"),
        "conclusion": run.get("conclusion") or None,
        "branch": run.get("headBranch", ""),
        "commit": run.get("headSha", ""),
        "event": run.get("event", ""),
        "created": run.get("createdAt", ""),
        "duration_seconds": duration_seconds(run),
        "url": run.get("url", ""),
    }


def summarize(runs, local_commit=None):

    completed = [
        run for run in runs
        if run["status"] == "completed"
    ]

    successes = [
        run for run in completed
        if run["conclusion"] == "success"
    ]

    failures = [
        run for run in completed
        if run["conclusion"] == "failure"
    ]

    active = [
        run for run in runs
        if run["status"] != "completed"
    ]

    durations = [
        run["duration_seconds"]
        for run in completed
        if run["duration_seconds"] is not None
    ]

    exact_runs = [
        run for run in runs
        if local_commit
        and run["commit"] == local_commit
    ]

    return {
        "total": len(runs),
        "completed": len(completed),
        "successful": len(successes),
        "failed": len(failures),
        "other_completed": (
            len(completed)
            - len(successes)
            - len(failures)
        ),
        "active": len(active),
        "success_rate": (
            round(
                len(successes)
                / len(completed) * 100, 1
            )
            if completed
            else None
        ),
        "average_duration_seconds": (
            round(sum(durations) / len(durations), 1)
            if durations
            else None
        ),
        "latest": runs[0] if runs else None,
        "exact_commit_runs": len(exact_runs),
        "exact_commit_success": any(
            run["status"] == "completed"
            and run["conclusion"] == "success"
            for run in exact_runs
        ),
    }


def pipeline_snapshot(limit=20):

    if not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100")

    local = local_repository()

    result = {
        "local": local,
        "available": False,
        "runs": [],
        "summary": summarize([], local["commit"]),
        "remote_main": None,
        "remote_error": None,
        "error": None,
        "timestamp": datetime.now().astimezone().isoformat(),
    }

    try:
        output = execute([
            "gh", "run", "list",
            "--repo", REPOSITORY,
            "--limit", str(limit),
            "--json", FIELDS,
        ])

        raw = json.loads(output)

        if not isinstance(raw, list):
            raise RuntimeError("Unexpected GitHub response")

        runs = [
            normalize_run(run)
            for run in raw
        ]

        result.update({
            "available": True,
            "runs": runs,
            "summary": summarize(
                runs, local["commit"]
            ),
        })

    except (
        RuntimeError,
        OSError,
        subprocess.TimeoutExpired,
        ValueError,
    ) as exc:

        result["error"] = str(exc)

        return result

    try:
        result["remote_main"] = execute([
            "gh", "api",
            f"repos/{REPOSITORY}/commits/main",
            "--jq", ".sha",
        ])

    except (
        RuntimeError,
        OSError,
        subprocess.TimeoutExpired,
    ) as exc:
        result["remote_error"] = str(exc)

    return result
