"""Read-only filesystem explorer and Linux academy."""

from textual import on
from textual.screen import Screen
from textual.containers import Horizontal
from textual.widgets import (
    Header,
    Footer,
    Static,
    ListView,
    ListItem,
    Label,
    RichLog,
)

from rich.text import Text

from nexus_ui.services.knowledge import (
    DIRECTORIES,
    LESSONS,
    inspect_directory,
)


class KnowledgeScreen(Screen):

    BINDINGS = [
        ("escape", "back", "Return"),
        ("f5", "refresh_content", "Refresh"),
    ]

    DEFAULT_CSS = """
    KnowledgeScreen {
        background: #080f17;
        color: #d7e6ed;
    }

    #knowledge-title {
        height: 3;
        padding: 1 2;
        background: #101d29;
        color: #40dfb7;
        text-style: bold;
    }

    #knowledge-body {
        height: 1fr;
        padding: 1;
    }

    #knowledge-navigation {
        width: 36;
        height: 1fr;
        border: round #245d5d;
        background: #101b26;
    }

    #knowledge-content {
        width: 1fr;
        height: 1fr;
        padding: 1 3;
        border: round #245d5d;
        background: #080f17;
    }

    #knowledge-navigation ListItem {
        padding: 0 1;
    }

    #knowledge-navigation ListItem.-highlight {
        background: #153b36;
        color: #40dfb7;
    }

    #knowledge-status {
        height: 2;
        padding: 0 2;
        color: #78a9b7;
    }
    """

    def __init__(self, mode="filesystem"):
        super().__init__()

        if mode not in {"filesystem", "academy"}:
            raise ValueError("Unknown knowledge workspace")

        self.mode = mode

        self.items = (
            list(DIRECTORIES)
            if mode == "filesystem"
            else [title for title, _ in LESSONS]
        )

    def compose(self):
        yield Header()

        title = (
            "FILESYSTEM INTELLIGENCE"
            if self.mode == "filesystem"
            else "LINUX ENGINEERING ACADEMY"
        )

        yield Static(
            f"NEXUS / {title}",
            id="knowledge-title",
        )

        with Horizontal(id="knowledge-body"):

            yield ListView(
                *[
                    ListItem(Label(item, markup=False))
                    for item in self.items
                ],
                id="knowledge-navigation",
            )

            yield RichLog(
                id="knowledge-content",
                wrap=True,
                markup=False,
            )

        yield Static(
            "READ-ONLY WORKSPACE / "
            "LOCAL LINUX ENGINEERING",
            id="knowledge-status",
        )

        yield Footer()

    def on_mount(self):
        navigation = self.query_one(
            "#knowledge-navigation", ListView
        )

        navigation.index = 0
        navigation.focus()

        self.show_content(0)

    @on(ListView.Highlighted, "#knowledge-navigation")
    def selection_changed(self, event):
        index = event.list_view.index

        if index is not None:
            self.show_content(index)

    def show_content(self, index):

        log = self.query_one(
            "#knowledge-content", RichLog
        )

        log.clear()

        def write(value, color="#d7e6ed"):
            log.write(Text(str(value), style=color))

        if self.mode == "academy":
            title, content = LESSONS[index]

            write(title, "bold #40dfb7")
            write("=" * 55, "#245d5d")
            write("")
            write(content)

            return

        data = inspect_directory(self.items[index])

        write(data["path"], "bold #40dfb7")
        write(data["title"], "bold #78a9b7")
        write("")
        write(data["description"])
        write("")
        write("LIVE SYSTEM METADATA", "bold #40dfb7")
        write("-" * 55, "#245d5d")

        if not data["available"]:
            write(
                data.get("error", "Unavailable"),
                "#ff7777",
            )
            return

        fields = [
            ("Resolved path", data["resolved"]),
            ("Owner", data["owner"]),
            ("Group", data["group"]),
            ("Permissions", data["permissions"]),
            ("Octal mode", data["octal"]),
            ("Readable", data["readable"]),
            ("Writable by you", data["writable"]),
        ]

        for label, value in fields:
            write(f"{label:20} {value}")

        write("")
        write("DIRECTORY ENTRIES", "bold #40dfb7")
        write("-" * 55, "#245d5d")

        if "listing_error" in data:
            write(data["listing_error"], "#e5bb72")
        else:
            for entry in data["entries"]:
                write(f"  {entry}")

            write("")
            write("Listing limited to 40 entries.")

        write("")
        write(
            "Read-only inspection. "
            "No file contents opened or modified.",
            "#78a9b7",
        )

    def action_refresh_content(self):
        navigation = self.query_one(
            "#knowledge-navigation", ListView
        )

        if navigation.index is not None:
            self.show_content(navigation.index)

    def action_back(self):
        self.app.pop_screen()
