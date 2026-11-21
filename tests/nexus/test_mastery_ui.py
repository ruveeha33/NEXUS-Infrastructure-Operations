import pytest

from textual.app import App
from textual.widgets import Input, Static

from nexus_ui.screens.mastery import MasteryScreen
from nexus_ui.services.mastery import CommandLab


@pytest.mark.asyncio
async def test_interactive_mission(tmp_path):

    lab = CommandLab(tmp_path / "lab")

    class TestApp(App):
        def on_mount(self):
            self.push_screen(MasteryScreen(lab))

    app = TestApp()

    async with app.run_test(size=(150, 48)) as pilot:

        await pilot.pause()

        commands = [
            "mkdir -p app/logs",
            "touch app/config.conf",
            "echo Started > app/logs/server.log",
            "pwd",
            "ls -R app",
            "mv app/logs/server.log app/logs/server.bak",
            "ls -l app/config.conf",
        ]

        for command in commands:
            field = app.screen.query_one(
                "#mastery-input", Input
            )

            field.value = command

            await pilot.press("enter")
            await pilot.pause()

        assert all(
            done for _, done in app.screen.mission_status()
        )

        assert len(lab.history) == 7

        assert (
            lab.root / "app/logs/server.bak"
        ).read_text() == "Started\n"

        await pilot.press("up")

        field = app.screen.query_one(
            "#mastery-input", Input
        )

        assert field.value == commands[-1]

        field.value = "cat /etc/passwd"

        await pilot.press("enter")
        await pilot.pause()

        assert not lab.history[-1].success

        await pilot.press("f2")
        await pilot.press("escape")
        await pilot.pause()

        assert not isinstance(app.screen, MasteryScreen)
