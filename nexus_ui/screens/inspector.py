import asyncio
from pathlib import Path

from rich.text import Text

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import (
    Static, Input, Button, DataTable, Footer
)
from textual import work

from nexus_ui.services import infrastructure as infra


VIEWS = {
    "processes": (
        "PROCESS INTELLIGENCE",
        ("PID", "PROCESS", "USER",
         "RAM MiB", "CPU SEC", "STATE"),
    ),
    "filesystem": (
        "FILESYSTEM INTELLIGENCE",
        ("NAME", "TYPE", "PERMISSIONS",
         "OWNER", "GROUP", "BYTES"),
    ),
    "network": (
        "NETWORK INTELLIGENCE",
        ("PROTOCOL", "LOCAL", "REMOTE",
         "STATE", "PID"),
    ),
    "interfaces": (
        "NETWORK INTERFACES",
        ("INTERFACE", "STATE", "FAMILY",
         "ADDRESS", "NETMASK"),
    ),
    "repository": (
        "REPOSITORY INTELLIGENCE",
        ("PROPERTY", "VALUE"),
    ),
    "commits": (
        "COMMIT HISTORY",
        ("COMMIT", "DATE", "DESCRIPTION"),
    ),
}


class Inspector(Screen):

    CSS = """
    Inspector {
        background: #080d14;
        color: #c8d7e5;
        padding: 0 1;
    }

    #inspector-title {
        height: 3;
        background: #10251f;
        color: #50dfb7;
        text-style: bold;
        padding: 1 2;
    }

    #inspector-toolbar {
        height: 3;
        margin: 1 0 0 0;
    }

    #inspector-toolbar Input {
        width: 1fr;
        background: #101a26;
        border: tall #263747;
        color: #c8d7e5;
    }

    #inspector-toolbar Button {
        min-width: 10;
        width: auto;
        height: 3;
        background: #193a36;
        color: #50dfb7;
        border: none;
        margin: 0 0 0 1;
    }

    #inspector-context {
        height: 2;
        color: #8299af;
        padding: 0 1;
    }

    #inspector-table {
        height: 1fr;
        border: round #263747;
        background: #080d14;
        color: #c8d7e5;
    }

    #inspector-table
    .datatable--header {
        background: #142331;
        color: #50dfb7;
        text-style: bold;
    }

    #inspector-table
    .datatable--cursor {
        background: #193a36;
        color: #50dfb7;
    }

    #inspector-status {
        height: 2;
        color: #50dfb7;
        padding: 0 1;
    }

    Inspector Footer {
        background: #101a26;
        color: #50dfb7;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("f5", "refresh_data", "Refresh"),
        Binding("f2", "alternate", "Switch view"),
        Binding("f3", "parent", "Parent directory"),
        Binding("f4", "sort", "Sort"),
    ]

    def __init__(self, mode):
        super().__init__()

        if mode not in VIEWS:
            raise ValueError(mode)

        self.mode = mode
        self.directory = Path(".")
        self.rows = []
        self.filtered = []
        self.sort_index = -1
        self.reverse = False

    def compose(self) -> ComposeResult:
        yield Static(
            f"◈ NEXUS / {VIEWS[self.mode][0]}",
            id="inspector-title",
        )

        with Horizontal(id="inspector-toolbar"):
            yield Input(
                placeholder="Search records...",
                id="inspector-search",
            )
            yield Button(
                "Refresh", id="inspect-refresh"
            )
            yield Button(
                "Switch", id="inspect-switch"
            )
            yield Button(
                "Back", id="inspect-back"
            )

        yield Static(
            "Initializing intelligence...",
            id="inspector-context",
        )

        yield DataTable(
            id="inspector-table",
            zebra_stripes=True,
            cursor_type="row",
        )

        yield Static(
            "Collecting records...",
            id="inspector-status",
        )

        yield Footer()

    def on_mount(self):
        self.configure_table()
        self.action_refresh_data()
        self.query_one("#inspector-search").focus()

        self.set_interval(5, self.auto_refresh)

    def auto_refresh(self):
        if self.mode in (
            "processes", "network", "interfaces"
        ):
            self.action_refresh_data()

    def configure_table(self):
        table = self.query_one(
            "#inspector-table", DataTable
        )

        table.clear(columns=True)
        table.add_columns(*VIEWS[self.mode][1])

        self.query_one("#inspector-title").update(
            f"◈ NEXUS / {VIEWS[self.mode][0]}"
        )

    @work(exclusive=True, group="inspector")
    async def action_refresh_data(self):
        mode = self.mode
        directory = self.directory

        try:
            function = {
                "processes": infra.processes,
                "filesystem": lambda: infra.filesystem(
                    directory
                ),
                "network": infra.connections,
                "interfaces": infra.interfaces,
                "repository": infra.repository,
                "commits": infra.commits,
            }[mode]

            rows = await asyncio.to_thread(function)

            if mode != self.mode:
                return

            self.rows = rows
            self.render_rows()

        except Exception as error:
            self.rows = []
            self.filtered = []
            self.query_one(
                "#inspector-table", DataTable
            ).clear()

            self.query_one(
                "#inspector-status"
            ).update(
                Text(
                    f"DATA UNAVAILABLE: {error}",
                    style="#ff7272",
                )
            )

    def render_rows(self):
        table = self.query_one(
            "#inspector-table", DataTable
        )

        term = self.query_one(
            "#inspector-search", Input
        ).value.lower()

        rows = [
            row for row in self.rows
            if term in " ".join(row).lower()
        ]

        if self.sort_index >= 0:
            index = self.sort_index

            def key(row):
                value = row[index].replace(",", "")
                try:
                    return (0, float(value))
                except ValueError:
                    return (1, value.lower())

            rows.sort(
                key=key, reverse=self.reverse
            )

        self.filtered = rows
        table.clear()

        for row in rows:
            table.add_row(
                *[Text(value) for value in row]
            )

        context = {
            "processes":
                "LIVE PROCESS INVENTORY | CPU SEC = accumulated CPU time",
            "filesystem":
                f"PROJECT PATH / {self.directory}",
            "network":
                "SOCKET INVENTORY | Visible connections for current user",
            "interfaces":
                "LOCAL NETWORK INTERFACES",
            "repository":
                "LOCAL GIT REPOSITORY",
            "commits":
                "MOST RECENT 15 COMMITS",
        }[self.mode]

        self.query_one(
            "#inspector-context"
        ).update(Text(context))

        self.query_one(
            "#inspector-status"
        ).update(
            f" {len(rows)} / {len(self.rows)} RECORDS"
            "  |  F5 REFRESH  |  ESC RETURN"
        )

    def on_input_changed(self, event):
        self.render_rows()

    def on_data_table_row_selected(self, event):
        if self.mode != "filesystem":
            return

        index = event.cursor_row

        if index >= len(self.filtered):
            return

        name, kind, *_ = self.filtered[index]

        if kind == "DIR":
            self.directory = self.directory / name
            self.action_refresh_data()

    def action_parent(self):
        if self.mode == "filesystem":
            self.directory = self.directory.parent
            self.action_refresh_data()

    def action_sort(self):
        count = len(VIEWS[self.mode][1])
        self.sort_index = (
            self.sort_index + 1
        ) % count
        self.reverse = True
        self.render_rows()

    def action_alternate(self):
        alternatives = {
            "network": "interfaces",
            "interfaces": "network",
            "repository": "commits",
            "commits": "repository",
        }

        if self.mode not in alternatives:
            self.notify(
                "Use search, refresh or sorting."
            )
            return

        self.mode = alternatives[self.mode]
        self.rows = []
        self.filtered = []
        self.sort_index = -1
        self.configure_table()
        self.action_refresh_data()

    def action_back(self):
        self.app.pop_screen()

    def on_button_pressed(self, event):
        action = {
            "inspect-refresh":
                self.action_refresh_data,
            "inspect-switch":
                self.action_alternate,
            "inspect-back":
                self.action_back,
        }.get(event.button.id)

        if action:
            action()
