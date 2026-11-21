import asyncio

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Static,
    Button,
    RichLog,
    Footer,
)

from nexus_ui.services.control import (
    service_status,
    perform,
    backup_inventory,
    operation_history,
)


class Confirmation(ModalScreen[bool]):

    CSS = """
    Confirmation {
        align: center middle;
    }

    Confirmation #dialog {
        width: 60;
        height: auto;
        border: round #d8a75b;
        background: #101a26;
        padding: 2;
    }

    Confirmation Horizontal {
        height: 3;
    }

    Confirmation Button {
        width: 1fr;
        height: 3;
    }
    """

    def __init__(self, operation):
        super().__init__()
        self.operation = operation

    def compose(self):
        from textual.containers import Vertical

        with Vertical(id="dialog"):
            yield Static(
                "CONFIRM SERVICE OPERATION\n\n"
                f"Action: {self.operation.upper()}\n"
                "Target: Linux Operations Lab only\n"
                "Endpoint: 127.0.0.1:8095\n\n"
                "This operation may interrupt availability."
            )

            with Horizontal():
                yield Button(
                    "Confirm", id="confirm"
                )
                yield Button(
                    "Cancel", id="cancel"
                )

    def on_mount(self):
        self.query_one("#cancel").focus()

    def on_button_pressed(self, event):
        self.dismiss(
            event.button.id == "confirm"
        )


class ServiceControl(Screen):

    CSS = """
    ServiceControl {
        background: #080d14;
        color: #c8d7e5;
        padding: 0 1;
    }

    #control-title {
        height: 3;
        background: #10251f;
        color: #50dfb7;
        padding: 1 2;
        text-style: bold;
    }

    #service-information {
        height: 11;
        border: round #35685d;
        padding: 1;
        background: #101a26;
    }

    #control-toolbar {
        height: 3;
        margin: 1 0;
    }

    #control-toolbar Button {
        width: 1fr;
        min-width: 8;
        height: 3;
        background: #193a36;
        color: #50dfb7;
        border: none;
        margin: 0 1 0 0;
    }

    #control-output {
        height: 1fr;
        border: round #263747;
        background: #0c1520;
        padding: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "Return"),
        Binding("f5", "refresh_status", "Refresh"),
    ]

    def __init__(self):
        super().__init__()
        self.busy = False

    def compose(self) -> ComposeResult:
        yield Static(
            "◈ NEXUS / OPERATIONAL CONTROL CENTER",
            id="control-title",
        )

        yield Static(
            "Collecting service intelligence...",
            id="service-information",
        )

        with Horizontal(id="control-toolbar"):
            yield Button(
                "Start", id="control-start"
            )
            yield Button(
                "Stop", id="control-stop"
            )
            yield Button(
                "Restart", id="control-restart"
            )
            yield Button(
                "Backups", id="control-backups"
            )
            yield Button(
                "History", id="control-history"
            )
            yield Button(
                "Return", id="control-back"
            )

        yield RichLog(
            id="control-output",
            wrap=True,
            markup=False,
            max_lines=2000,
        )

        yield Footer()

    def on_mount(self):
        self.action_refresh_status()
        self.set_interval(
            5, self.action_refresh_status
        )

        self.query_one(
            "#control-output", RichLog
        ).write(
            Text(
                "CONTROL ENGINE READY\n"
                "Only the verified lab service "
                "can be managed.",
                style="#50dfb7",
            )
        )

    @work(exclusive=True, group="service-status")
    async def action_refresh_status(self):
        status = await asyncio.to_thread(
            service_status
        )

        health = status["health"]

        state = (
            "OPERATIONAL"
            if health["online"]
            else "UNAVAILABLE"
        )

        ownership = (
            "VERIFIED"
            if status["managed"]
            else "NOT VERIFIED"
        )

        self.query_one(
            "#service-information", Static
        ).update(
            Text(
                "MANAGED SERVICE / LINUX OPERATIONS LAB\n\n"
                f"Availability       {state}\n"
                f"Process ownership  {ownership}\n"
                f"Process ID         {status['pid']}\n"
                f"Uptime             {status['uptime']} sec\n"
                f"Memory             {status['memory_mib']} MiB\n"
                f"HTTP response      {health['status']}\n"
                f"Latency            {health['latency']} ms",
                style="#50dfb7"
                if health["online"]
                else "#e6b45c",
            )
        )

    def on_button_pressed(self, event):
        operation = (
            event.button.id or ""
        ).removeprefix("control-")

        if operation == "back":
            self.action_back()
            return

        if self.busy:
            self.notify(
                "An operation is already running."
            )
            return

        if operation in (
            "start", "stop", "restart"
        ):
            self.app.push_screen(
                Confirmation(operation),
                lambda confirmed: (
                    self.begin_operation(operation)
                    if confirmed else None
                ),
            )

        elif operation == "backups":
            self.show_backups()

        elif operation == "history":
            self.show_history()

    def begin_operation(self, operation):
        if not self.busy:
            self.busy = True
            self.execute(operation)

    @work(group="service-operation")
    async def execute(self, operation):
        output = self.query_one(
            "#control-output", RichLog
        )

        output.clear()
        output.write(
            f"EXECUTING / {operation.upper()}"
        )

        try:
            success, detail = await asyncio.to_thread(
                perform, operation
            )

            output.write(
                Text(
                    detail,
                    style="#50dfb7"
                    if success else "#ff7272",
                )
            )

        except Exception as error:
            output.write(
                Text(
                    str(error),
                    style="#ff7272",
                )
            )

        finally:
            self.busy = False
            self.action_refresh_status()

    @work(exclusive=True, group="inventory")
    async def show_backups(self):
        output = self.query_one(
            "#control-output", RichLog
        )

        output.clear()
        output.write("BACKUP ARCHIVE INVENTORY\n")

        try:
            rows = await asyncio.to_thread(
                backup_inventory
            )

            for name, size, digest in rows:
                output.write(
                    Text(
                        f"ARCHIVE  {name}\n"
                        f"SIZE     {size} bytes\n"
                        f"SHA-256  {digest}\n",
                        style="#a8bbcd",
                    )
                )

            output.write(
                f"TOTAL ARCHIVES: {len(rows)}"
            )

        except Exception as error:
            output.write(str(error))

    @work(exclusive=True, group="inventory")
    async def show_history(self):
        output = self.query_one(
            "#control-output", RichLog
        )

        output.clear()

        events = await asyncio.to_thread(
            operation_history
        )

        output.write("SERVICE OPERATION HISTORY\n")

        for event in events:
            result = (
                "PASS" if event["success"]
                else "FAIL"
            )

            output.write(
                f"{event['timestamp']} "
                f"[{result}] "
                f"{event['operation'].upper()}\n"
                f"{event['detail']}\n"
            )

        if not events:
            output.write(
                "No recorded service operations."
            )

    def action_back(self):
        if self.busy:
            self.notify(
                "Wait for the current operation."
            )
            return

        self.app.pop_screen()
