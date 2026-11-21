"""NEXUS terminal layout and navigation acceptance tests."""

import pytest

from nexus_ui.app import Nexus
from nexus_ui.widgets.compact_graph import CompactGraph


SIZES = (
    (160, 48),
    (120, 40),
    (100, 32),
    (80, 24),
)

NAVIGATION = (
    "overview",
    "operations",
    "services",
    "logs",
    "processes",
    "network",
    "filesystem",
    "audit",
    "backup",
    "recover",
    "incidents",
    "repository",
    "pipeline",
    "verify",
    "reports",
    "mastery",
    "fhs",
    "academy",
    "ssh-lab",
)


@pytest.mark.asyncio
@pytest.mark.parametrize("size", SIZES)
async def test_navigation_structure(size):

    app = Nexus()

    async with app.run_test(size=size) as pilot:

        await pilot.pause()

        buttons = list(
            app.query("#navigation Button")
        )

        assert len(buttons) == len(NAVIGATION)

        actual = {
            button.id
            for button in buttons
        }

        expected = {
            f"nav-{name}"
            for name in NAVIGATION
        }

        assert actual == expected

        navigation = app.query_one("#navigation")

        assert navigation.size.width > 0
        assert navigation.size.height > 0


@pytest.mark.asyncio
@pytest.mark.parametrize("size", SIZES)
async def test_dashboard_components(size):

    app = Nexus()

    async with app.run_test(size=size) as pilot:

        await pilot.pause()

        for name in ("cpu", "memory", "disk"):

            graph = app.query_one(
                f"#{name}-graph",
                CompactGraph,
            )

            assert graph.size.width > 0

            graph.set_samples(
                [0.1, 1.2, 4.5, 2.1]
            )

            assert len(graph.samples) == 4

        for ident in (
            "health",
            "system",
            "traffic",
            "processes",
            "report",
            "assurance",
            "statusbar",
        ):

            assert app.query_one(
                f"#{ident}"
            ) is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("size", SIZES)
async def test_primary_navigation(size):

    app = Nexus()

    async with app.run_test(size=size) as pilot:

        await pilot.pause()

        await pilot.press("2")
        await pilot.pause()

        assert app.query_one(
            "#operations"
        ).display

        await pilot.press("1")
        await pilot.pause()

        assert app.query_one(
            "#workspace"
        ).display


@pytest.mark.asyncio
@pytest.mark.parametrize("size", SIZES)
async def test_engineering_workspace(size):

    app = Nexus()

    async with app.run_test(size=size) as pilot:

        await pilot.pause()

        await pilot.press("r")
        await pilot.pause()

        assert (
            type(app.screen).__name__
            == "ReportsScreen"
        )

        await pilot.press("escape")
        await pilot.pause()


@pytest.mark.asyncio
async def test_sidebar_buttons_are_keyboard_accessible():

    app = Nexus()

    async with app.run_test(
        size=(100, 32)
    ) as pilot:

        await pilot.pause()

        navigation = app.query_one("#navigation")

        assert navigation.can_focus

        for name in NAVIGATION:

            button = app.query_one(
                f"#nav-{name}"
            )

            assert not button.disabled


@pytest.mark.asyncio
async def test_dashboard_recovers_after_resize():

    app = Nexus()

    async with app.run_test(
        size=(160, 48)
    ) as pilot:

        await pilot.pause()

        app._driver._size = (80, 24)

        app.refresh(layout=True)

        await pilot.pause()

        assert app.query_one(
            "#navigation"
        ).size.width > 0

        assert app.query_one(
            "#health"
        ) is not None
