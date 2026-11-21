"""Regression tests for failed NEXUS service startup."""

from unittest.mock import MagicMock, patch

import pytest

from nexus_ui.services import control


def test_failed_startup_cleans_up_its_process(tmp_path):
    process = MagicMock()
    process.pid = 424242
    process.poll.return_value = None

    with (
        patch.object(control, "PID_FILE", tmp_path / "server.pid"),
        patch.object(control, "LOG_FILE", tmp_path / "server.log"),
        patch.object(control, "managed_process", return_value=None),
        patch.object(control, "port_occupied", return_value=False),
        patch.object(control, "http_health", return_value={"online": False}),
        patch.object(control.subprocess, "Popen", return_value=process),
        patch.object(control.time, "sleep"),
    ):
        with pytest.raises(
            RuntimeError,
            match="Newly launched process cleaned up",
        ):
            control.start_service()

    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=5)
    assert not (tmp_path / "server.pid").exists()


def test_failed_startup_escalates_after_timeout(tmp_path):
    process = MagicMock()
    process.pid = 424243
    process.poll.return_value = None
    process.wait.side_effect = [
        control.subprocess.TimeoutExpired("server", 5),
        None,
    ]

    with (
        patch.object(control, "PID_FILE", tmp_path / "server.pid"),
        patch.object(control, "LOG_FILE", tmp_path / "server.log"),
        patch.object(control, "managed_process", return_value=None),
        patch.object(control, "port_occupied", return_value=False),
        patch.object(control, "http_health", return_value={"online": False}),
        patch.object(control.subprocess, "Popen", return_value=process),
        patch.object(control.time, "sleep"),
    ):
        with pytest.raises(
            RuntimeError,
            match="Newly launched process cleaned up",
        ):
            control.start_service()

    process.terminate.assert_called_once()
    process.kill.assert_called_once()
    assert process.wait.call_count == 2
    assert not (tmp_path / "server.pid").exists()
