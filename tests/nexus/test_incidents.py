import json
import pytest

from nexus_ui.services.incidents import (
    SCENARIOS,
    run_incident,
)


@pytest.mark.parametrize(
    "scenario",
    list(SCENARIOS),
)
def test_incident_recovery(tmp_path, scenario):

    result = run_incident(
        scenario,
        emit=lambda line: None,
        evidence_dir=tmp_path,
    )

    assert result.detected
    assert result.recovered
    assert result.root_cause
    assert result.duration_ms >= 0

    reports = list(tmp_path.glob("*.json"))

    assert len(reports) == 1

    data = json.loads(reports[0].read_text())

    assert data["scenario"] == scenario
    assert data["detected"]
    assert data["recovered"]

    stages = {
        event["stage"]
        for event in data["events"]
    }

    assert {
        "baseline",
        "inject",
        "detect",
        "diagnose",
        "recover",
        "verify",
        "cleanup",
    }.issubset(stages)


def test_invalid_scenario(tmp_path):

    with pytest.raises(ValueError):

        run_incident(
            "unknown",
            evidence_dir=tmp_path,
        )

    assert not list(tmp_path.iterdir())
