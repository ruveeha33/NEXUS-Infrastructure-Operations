import pytest

from textual.widgets import DataTable

from nexus_ui.screens import pipeline


def fixture_snapshot():

    return {
        "available": True,
        "local": {
            "repository": "example/repository",
            "branch": "feature",
            "commit": "abc123",
            "dirty": True,
        },
        "remote_main": "abc123",
        "timestamp": "TEST FIXTURE",
        "summary": {
            "successful": 1,
            "failed": 0,
            "success_rate": 100,
            "average_duration_seconds": 8,
            "total": 1,
            "active": 0,
            "exact_commit_success": True,
        },
        "runs": [{
            "id": 123,
            "workflow": "Verification",
            "branch": "main",
            "commit": "abc123",
            "status": "completed",
            "conclusion": "success",
            "duration_seconds": 8,
        }],
    }


@pytest.mark.asyncio
async def test_pipeline_ui(monkeypatch):

    from nexus_ui.app import Nexus

    monkeypatch.setattr(
        pipeline,
        "pipeline_snapshot",
        fixture_snapshot,
    )

    app = Nexus()

    async with app.run_test(
        size=(150, 48)
    ) as pilot:

        await pilot.pause()
        await pilot.press("c")

        for _ in range(100):

            await pilot.pause(0.05)

            if (
                isinstance(
                    app.screen,
                    pipeline.PipelineScreen,
                )
                and not app.screen.running
            ):
                break

        screen = app.screen

        assert isinstance(
            screen, pipeline.PipelineScreen
        )

        assert screen.snapshot is not None

        table = screen.query_one(
            "#pipeline-history", DataTable
        )

        assert table.row_count == 1

        await pilot.press("escape")
        await pilot.pause()

        assert not isinstance(
            app.screen, pipeline.PipelineScreen
        )


@pytest.mark.asyncio
async def test_pipeline_offline(monkeypatch):

    from nexus_ui.app import Nexus

    monkeypatch.setattr(
        pipeline,
        "pipeline_snapshot",
        lambda: {"available": False},
    )

    app = Nexus()

    async with app.run_test(
        size=(150, 48)
    ) as pilot:

        await pilot.pause()
        await pilot.press("c")

        for _ in range(100):

            await pilot.pause(0.05)

            if (
                isinstance(
                    app.screen,
                    pipeline.PipelineScreen,
                )
                and not app.screen.running
            ):
                break

        screen = app.screen

        assert isinstance(
            screen, pipeline.PipelineScreen
        )

        assert not screen.running
        assert screen.snapshot is None

        assert screen.query_one(
            "#pipeline-history", DataTable
        ).row_count == 0

        await pilot.press("escape")
        await pilot.pause()
