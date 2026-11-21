import asyncio
import pytest

from textual.app import App

from nexus_ui.screens.incidents import IncidentScreen


@pytest.mark.asyncio
async def test_run_all():

    class TestApp(App):
        def on_mount(self):
            self.push_screen(IncidentScreen())

    app = TestApp()

    async with app.run_test(
        size=(150, 48)
    ) as pilot:

        await pilot.pause()

        screen = app.screen

        await pilot.click("#incident-all")

        for _ in range(200):

            await pilot.pause(0.05)

            if screen.attempts == 5 and not screen.running:
                break

        assert screen.attempts == 5
        assert screen.detected == 5
        assert screen.recovered == 5
        assert not screen.running

        await pilot.press("escape")
        await pilot.pause()

        assert not isinstance(
            app.screen, IncidentScreen
        )


@pytest.mark.asyncio
async def test_navigation():

    from nexus_ui.app import Nexus

    app = Nexus()

    async with app.run_test(
        size=(150, 48)
    ) as pilot:

        await pilot.pause()
        await pilot.press("i")
        await pilot.pause()

        assert isinstance(
            app.screen, IncidentScreen
        )

        await pilot.press("escape")
        await pilot.pause()

        assert not isinstance(
            app.screen, IncidentScreen
        )
