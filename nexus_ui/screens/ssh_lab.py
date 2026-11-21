"""Interactive SSH engineering workspace."""

from rich.text import Text

from textual import on, work
from textual.screen import Screen
from textual.containers import Horizontal
from textual.widgets import (
    Header,
    Footer,
    Static,
    Button,
    RichLog,
)

from nexus_ui.services.ssh_lab import ssh_mission


class SSHLabScreen(Screen):

    BINDINGS = [
        ("escape", "back", "Return"),
    ]

    DEFAULT_CSS = """
    SSHLabScreen {
        background: #080f17;
        color: #d7e6ed;
    }

    #ssh-title {
        height: 3;
        padding: 1 2;
        background: #101d29;
        color: #40dfb7;
        text-style: bold;
    }

    #ssh-status {
        height: 3;
        padding: 1 2;
        color: #40dfb7;
    }

    #ssh-transcript {
        height: 1fr;
        margin: 0 1;
        padding: 1 2;
        border: round #245d5d;
        background: #080f17;
    }

    #ssh-controls {
        height: 3;
        padding: 0 1;
    }

    #ssh-controls Button {
        margin-right: 2;
    }
    """

    def __init__(self):
        super().__init__()
        self.running = False

    def compose(self):
        yield Header()

        yield Static(
            "NEXUS / SECURE SHELL ENGINEERING",
            id="ssh-title",
        )

        yield Static(
            "127.0.0.1:22222 | ED25519 | READY",
            id="ssh-status",
        )

        yield RichLog(
            id="ssh-transcript",
            wrap=True,
            markup=False,
            max_lines=1000,
        )

        with Horizontal(id="ssh-controls"):

            yield Button(
                "Run SSH Mission",
                id="ssh-run",
                variant="success",
            )

            yield Button(
                "Return",
                id="ssh-return",
            )

        yield Footer()

    def on_mount(self):
        self.write("LOCAL SSH TRAINING WORKSPACE")
        self.write("Real OpenSSH authentication.")
        self.write("Temporary keys and server lifecycle.")
        self.write("Standard SSH service remains disabled.")
        self.write("Select Run SSH Mission to begin.")

    def write(self, message):
        color = "#d7e6ed"

        if message.startswith("[PASS]"):
            color = "#40dfb7"

        elif message.startswith("[FAIL]"):
            color = "#ff7777"

        self.query_one(
            "#ssh-transcript", RichLog
        ).write(Text(message, style=color))

    @on(Button.Pressed, "#ssh-run")
    def start_mission(self):

        if self.running:
            return

        self.running = True

        self.query_one("#ssh-run", Button).disabled = True
        self.query_one("#ssh-return", Button).disabled = True

        self.query_one(
            "#ssh-transcript", RichLog
        ).clear()

        self.query_one("#ssh-status", Static).update(
            "SSH MISSION RUNNING"
        )

        self.execute_mission()

    @work(thread=True, exclusive=True)
    def execute_mission(self):

        try:

            ssh_mission(
                emit=lambda line: self.app.call_from_thread(
                    self.write, line
                )
            )

            status = "MISSION PASSED / SESSION CLOSED"

        except Exception as exc:

            self.app.call_from_thread(
                self.write,
                f"[FAIL] {exc}",
            )

            status = "MISSION FAILED / CHECK TRANSCRIPT"

        finally:
            self.app.call_from_thread(
                self.finish_mission,
                status,
            )

    def finish_mission(self, status):

        self.running = False

        self.query_one(
            "#ssh-status", Static
        ).update(status)

        self.query_one("#ssh-run", Button).disabled = False
        self.query_one("#ssh-return", Button).disabled = False

    @on(Button.Pressed, "#ssh-return")
    def return_pressed(self):
        self.action_back()

    def action_back(self):

        if self.running:
            self.notify("Wait for SSH session cleanup.")
            return

        self.app.pop_screen()
