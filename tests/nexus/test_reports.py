import json

from nexus_ui.services import reports


def test_incident_summary(tmp_path):

    (tmp_path / "valid.json").write_text(
        json.dumps({
            "scenario": "outage",
            "detected": True,
            "recovered": True,
        })
    )

    (tmp_path / "invalid.json").write_text(
        "invalid JSON"
    )

    data = reports.incident_summary(tmp_path)

    assert data["total"] == 1
    assert data["detected"] == 1
    assert data["recovered"] == 1
    assert data["recovery_rate"] == 100
    assert data["invalid_records"] == 1


def test_empty_incidents(tmp_path):

    data = reports.incident_summary(tmp_path)

    assert data["total"] == 0
    assert data["recovery_rate"] is None


def test_dirty_release():

    result = reports.release_assessment(
        {"online": True},
        {"passed": True},
        {"passed": True},
        {
            "available": True,
            "local": {"dirty": True},
            "summary": {
                "exact_commit_success": True
            },
        },
    )

    assert result["local_status"] == "PASSED"
    assert result["release_status"] == "DEVELOPMENT"


def test_offline_release():

    result = reports.release_assessment(
        {"online": True},
        {"passed": True},
        {"passed": True},
        {"available": False},
    )

    assert result["release_status"] == "NOT VERIFIED"


def test_failed_security():

    result = reports.release_assessment(
        {"online": True},
        {"passed": False},
        {"passed": True},
        {"available": False},
    )

    assert result["release_status"] == "NOT READY"


def test_checksum(tmp_path):

    path = tmp_path / "example"

    path.write_bytes(b"abc")

    assert reports.checksum(path) == (
        "ba7816bf8f01cfea414140de5dae2223"
        "b00361a396177a9cb410ff61f20015ad"
    )
