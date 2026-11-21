"""Interactive Linux command laboratory."""

from pathlib import Path
from tempfile import mkdtemp
from datetime import datetime

from rich.text import Text

from textual import on
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Static,
    Input,
    RichLog,
    Header,
    Footer,
)

from nexus_ui.services.mastery import CommandLab, LAB


class CommandInput(Input):

    def on_key(self, event):
        if event.key == "up":
            self.screen.recall(-1)
            event.stop()
            event.prevent_default()

        elif event.key == "down":
            self.screen.recall(1)
            event.stop()
            event.prevent_default()


class MasteryScreen(Screen):

    BINDINGS = [
        ("f1", "help", "Help"),
        ("f2", "clear", "Clear"),
        ("f5", "refresh_lab", "Refresh"),
        ("escape", "back", "Return"),
    ]

    DEFAULT_CSS = """
    MasteryScreen {
        background: #080f17;
        color: #d7e6ed;
    }

    #mastery-title {
        height: 3;
        padding: 1 2;
        color: #40dfb7;
        text-style: bold;
        background: #101d29;
    }

    #mastery-metrics {
        height: 3;
        padding: 1 2;
        color: #40dfb7;
    }

    #mastery-body {
        height: 1fr;
        padding: 0 1;
    }

    #mastery-terminal {
        width: 2fr;
        height: 1fr;
        border: round #245d5d;
        padding: 0 1;
        background: #080f17;
    }

    #mastery-sidebar {
        width: 1fr;
        height: 1fr;
        padding: 1 2;
        border: round #245d5d;
        background: #101b26;
    }

    #mastery-mission {
        height: auto;
        color: #d7e6ed;
    }

    #mastery-location {
        height: 2;
        padding: 0 2;
        color: #78a9b7;
    }

    #mastery-input {
        margin: 0 1;
        border: round #40dfb7;
        background: #0c1a23;
        color: #40dfb7;
    }
    """

    def __init__(self, lab=None):
        super().__init__()

        if lab is None:
            LAB.mkdir(parents=True, exist_ok=True)
            lab = CommandLab(
                Path(mkdtemp(prefix="session-", dir=LAB))
            )

        self.lab = lab
        self.command_history = []
        self.history_index = 0

    def compose(self):
        yield Header()

        yield Static(
            "NEXUS / LINUX ENGINEERING / COMMAND LAB",
            id="mastery-title",
        )

        yield Static("", id="mastery-metrics")

        with Horizontal(id="mastery-body"):
            yield RichLog(
                id="mastery-terminal",
                wrap=True,
                markup=False,
                max_lines=1500,
            )

            with Vertical(id="mastery-sidebar"):
                yield Static(
                    "",
                    id="mastery-mission",
                    markup=False,
                )

        yield Static(
            "",
            id="mastery-location",
            markup=False,
        )

        yield CommandInput(
            placeholder="Enter Linux command or help",
            id="mastery-input",
        )

        yield Footer()

    def on_mount(self):
        self.write(
            "NEXUS LINUX ENGINEERING WORKSPACE",
            "bold #40dfb7",
        )

        self.write(
            "Real Linux executables. Restricted commands."
        )

        self.write(
            "Practice files are separated from the application."
        )

        self.write("Type help to view available commands.")

        self.refresh_metrics()
        self.query_one("#mastery-input", Input).focus()

    def write(self, content, style=""):
        self.query_one(
            "#mastery-terminal", RichLog
        ).write(Text(str(content), style=style))

    def mission_status(self):
        app = self.lab.root / "app"
        config = app / "config.conf"
        log = app / "logs" / "server.log"
        backup = app / "logs" / "server.bak"

        def has_started(path):
            try:
                return (
                    path.is_file()
                    and path.read_text().strip() == "Started"
                )
            except (OSError, UnicodeError):
                return False

        commands = [
            result.command.strip()
            for result in self.lab.history
            if result.success
        ]

        return [
            (
                "Directory structure",
                (app / "logs").is_dir(),
            ),
            (
                "Configuration file",
                config.is_file(),
            ),
            (
                "Log initialization",
                has_started(log) or has_started(backup),
            ),
            (
                "Navigation and listing",
                "pwd" in commands
                and "ls -R app" in commands,
            ),
            (
                "Log rotation",
                has_started(backup)
                and not log.exists(),
            ),
            (
                "Permission inspection",
                "ls -l app/config.conf" in commands,
            ),
        ]

    def refresh_metrics(self):
        total = len(self.lab.history)

        passed = sum(
            result.success
            for result in self.lab.history
        )

        rate = (passed / total * 100) if total else 0

        self.query_one("#mastery-metrics", Static).update(
            f"COMMANDS {total:03d}   "
            f"SUCCESS {passed:03d}   "
            f"RATE {rate:.0f}%   "
            f"SESSION LOCAL"
        )

        objectives = self.mission_status()

        completed = sum(
            done for _, done in objectives
        )

        lines = [
            "DECODELABS / INTERN MISSION",
            "--------------------------------",
            "",
        ]

        for title, done in objectives:
            status = "[PASS]" if done else "[....]"
            lines.append(f"{status} {title}")
            lines.append("")

        lines.extend([
            "--------------------------------",
            f"PROGRESS: {completed}/6",
            "",
            "SUGGESTED COMMANDS",
            "",
            "mkdir -p app/logs",
            "touch app/config.conf",
            "echo Started > app/logs/server.log",
            "pwd",
            "ls -R app",
            "mv app/logs/server.log app/logs/server.bak",
            "ls -l app/config.conf",
        ])

        self.query_one("#mastery-mission", Static).update(
            "\n".join(lines)
        )

        self.query_one("#mastery-location", Static).update(
            f"WORKING DIRECTORY: {self.lab.cwd}"
        )

    @on(Input.Submitted, "#mastery-input")
    def submit_command(self, event):
        command = event.value.strip()

        if not command:
            return

        self.command_history.append(command)
        self.history_index = len(self.command_history)

        event.input.value = ""

        self.write(
            f"\nengineer@nexus$ {command}",
            "bold #40dfb7",
        )

        result = self.lab.run(command)

        self.write(
            result.output,
            "#d7e6ed" if result.success else "#ff7777",
        )

        timestamp = datetime.now().strftime("%H:%M:%S")

        self.write(
            f"[{timestamp}] "
            f"{'SUCCESS' if result.success else 'REJECTED'}",
            "#40dfb7" if result.success else "#ff7777",
        )

        self.refresh_metrics()

    def recall(self, direction):
        self.history_index = max(
            0,
            min(
                len(self.command_history),
                self.history_index + direction,
            ),
        )

        field = self.query_one("#mastery-input", Input)

        field.value = (
            self.command_history[self.history_index]
            if self.history_index < len(self.command_history)
            else ""
        )

        field.cursor_position = len(field.value)

    def action_help(self):
        self.write(self.lab.run("help").output)
        self.refresh_metrics()

    def action_clear(self):
        self.query_one("#mastery-terminal", RichLog).clear()

    def action_refresh_lab(self):
        self.refresh_metrics()

    def action_back(self):
        self.app.pop_screen()
