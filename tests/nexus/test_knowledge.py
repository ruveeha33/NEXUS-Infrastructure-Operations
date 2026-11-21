import pytest

from textual.app import App
from textual.widgets import ListView

from nexus_ui.services.knowledge import (
    DIRECTORIES,
    LESSONS,
    inspect_directory,
)

from nexus_ui.screens.knowledge import KnowledgeScreen


def test_required_fhs_directories():

    required = {
        "/", "/bin", "/boot", "/dev", "/etc",
        "/home", "/root", "/sbin", "/tmp",
        "/usr", "/var",
    }

    assert required.issubset(DIRECTORIES)


def test_real_filesystem_metadata():

    result = inspect_directory("/etc")

    assert result["available"]
    assert result["owner"]
    assert result["permissions"]
    assert len(result["entries"]) <= 40


def test_directory_boundary():

    with pytest.raises(ValueError):
        inspect_directory("/etc/passwd")


def test_academy_content():

    assert len(LESSONS) == 9

    combined = "\n".join(
        content for _, content in LESSONS
    )

    for term in [
        "pwd", "chmod", "chown",
        "ssh", "tail -f", "rm -rf",
        "mkdir -p app/logs",
    ]:
        assert term in combined


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mode", ["filesystem", "academy"]
)
async def test_knowledge_navigation(mode):

    class TestApp(App):
        def on_mount(self):
            self.push_screen(KnowledgeScreen(mode))

    app = TestApp()

    async with app.run_test(size=(150, 48)) as pilot:

        await pilot.pause()

        navigation = app.screen.query_one(
            ListView
        )

        assert navigation.index == 0

        await pilot.press("down")
        await pilot.pause()

        assert navigation.index == 1

        await pilot.press("f5")
        await pilot.press("escape")
        await pilot.pause()

        assert not isinstance(
            app.screen, KnowledgeScreen
        )
