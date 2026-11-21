import pytest

from nexus_ui.services.pipeline import (
    duration_seconds,
    normalize_run,
    summarize,
    local_repository,
    pipeline_snapshot,
)


def sample(
    status="completed",
    conclusion="success",
    commit="abc123",
):

    return normalize_run({
        "databaseId": 123,
        "workflowName": "Linux verification",
        "status": status,
        "conclusion": conclusion,
        "headSha": commit,
        "headBranch": "main",
        "startedAt": "2026-11-21T07:00:00Z",
        "updatedAt": "2026-11-21T07:00:06Z",
    })


def test_duration():

    assert sample()["duration_seconds"] == 6


def test_active_duration():

    assert sample(
        status="in_progress",
        conclusion="",
    )["duration_seconds"] is None


def test_missing_duration():

    assert duration_seconds({
        "status": "completed",
    }) is None


def test_summary():

    runs = [
        sample(),
        sample(conclusion="failure"),
        sample(conclusion="cancelled"),
        sample(
            status="in_progress",
            conclusion="",
        ),
    ]

    result = summarize(runs, "abc123")

    assert result["total"] == 4
    assert result["completed"] == 3
    assert result["successful"] == 1
    assert result["failed"] == 1
    assert result["other_completed"] == 1
    assert result["active"] == 1
    assert result["success_rate"] == 33.3
    assert result["exact_commit_success"]


def test_empty_history():

    result = summarize([])

    assert result["total"] == 0
    assert result["success_rate"] is None
    assert result["latest"] is None


def test_commit_verification():

    result = summarize(
        [sample(commit="old-commit")],
        "new-commit",
    )

    assert result["exact_commit_runs"] == 0
    assert not result["exact_commit_success"]


def test_local_repository():

    local = local_repository()

    assert len(local["commit"]) in (40, 64)
    assert local["repository"]


def test_invalid_limit():

    with pytest.raises(ValueError):
        pipeline_snapshot(101)


def test_remote_failure(monkeypatch):

    from nexus_ui.services import pipeline

    local = {
        "commit": "abc123",
        "branch": "main",
    }

    monkeypatch.setattr(
        pipeline,
        "local_repository",
        lambda: local,
    )

    def unavailable(*args, **kwargs):
        raise RuntimeError("Network unavailable")

    monkeypatch.setattr(
        pipeline,
        "execute",
        unavailable,
    )

    result = pipeline_snapshot()

    assert not result["available"]
    assert result["error"] == "Network unavailable"
    assert result["runs"] == []
    assert result["summary"]["success_rate"] is None
