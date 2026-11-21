"""Interactive engineering assurance workspace."""

from pathlib import Path

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

from nexus_ui.services.reports import generate_report

from nexus_ui.services.report_archive import (
    list_reports,
    load_latest,
    verify_report,
)


class ReportsScreen(Screen):

    BINDINGS = [
        ("escape", "back", "Return"),
    ]

    DEFAULT_CSS = """
    ReportsScreen {
        background: #080f17;
        color: #d7e6ed;
    }

    #report-title {
        height: 3;
        padding: 1 2;
        background: #101d29;
        color: #40dfb7;
        text-style: bold;
    }

    #report-metrics {
        height: 5;
        padding: 0 1;
    }

    .report-metric {
        width: 1fr;
        height: 5;
        border: round #245d5d;
        content-align: center middle;
        color: #40dfb7;
        text-style: bold;
    }

    #report-transcript {
        height: 1fr;
        margin: 1;
        border: round #245d5d;
        padding: 1 2;
        background: #080f17;
    }

    #report-status {
        height: 2;
        padding: 0 2;
        color: #40dfb7;
    }

    #report-controls {
        height: 3;
        padding: 0 1;
    }

    #report-controls Button {
        margin-right: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.running = False
        self.current_report = None

    def compose(self):

        yield Header()

        yield Static(
            "NEXUS / ENGINEERING ASSURANCE CENTER",
            id="report-title",
        )

        with Horizontal(id="report-metrics"):

            for key, label in (
                ("local", "LOCAL CHECKS"),
                ("integrity", "INTEGRITY"),
                ("release", "RELEASE"),
            ):

                yield Static(
                    f"{label}\n--",
                    id=f"report-{key}",
                    classes="report-metric",
                )

        yield RichLog(
            id="report-transcript",
            wrap=True,
            markup=False,
            max_lines=3000,
        )

        yield Static(
            "REPORT CENTER READY",
            id="report-status",
        )

        with Horizontal(id="report-controls"):

            yield Button(
                "Generate Report",
                id="report-generate",
                variant="success",
            )

            yield Button(
                "Latest Report",
                id="report-latest",
            )

            yield Button(
                "Verify Integrity",
                id="report-verify",
            )

            yield Button(
                "Return",
                id="report-return",
            )

        yield Footer()

    def on_mount(self):

        self.write("ENGINEERING REPORT CENTER")
        self.write("")
        self.write("Generate live engineering evidence.")
        self.write("Review the latest archived report.")
        self.write("Verify exported SHA-256 checksums.")

    def write(self, message, color="#d7e6ed"):

        self.query_one(
            "#report-transcript", RichLog
        ).write(Text(str(message), style=color))

    def begin(self, operation):

        if self.running:
            return

        self.running = True

        for button in self.query(Button):
            button.disabled = True

        self.query_one(
            "#report-transcript", RichLog
        ).clear()

        self.query_one(
            "#report-status", Static
        ).update("ENGINEERING OPERATION IN PROGRESS")

        self.execute(operation)

    @on(Button.Pressed, "#report-generate")
    def generate_pressed(self):
        self.begin("generate")

    @on(Button.Pressed, "#report-latest")
    def latest_pressed(self):
        self.begin("latest")

    @on(Button.Pressed, "#report-verify")
    def verify_pressed(self):
        self.begin("verify")

    @work(thread=True, exclusive=True)
    def execute(self, operation):

        status = "OPERATION COMPLETE"

        try:

            if operation == "generate":

                result = generate_report(
                    emit=lambda message:
                        self.app.call_from_thread(
                            self.write,
                            message,
                            "#78a9b7",
                        )
                )

                result["integrity"] = verify_report(
                    result["directory"]
                )

                self.app.call_from_thread(
                    self.display_report,
                    result,
                )

            elif operation == "latest":

                result = load_latest()

                if result is None:

                    self.app.call_from_thread(
                        self.write,
                        "No archived reports found.",
                    )

                    status = "NO REPORTS AVAILABLE"

                else:

                    self.app.call_from_thread(
                        self.display_report,
                        result,
                    )

            elif operation == "verify":

                folder = self.current_report

                if folder is None:

                    folders = list_reports()

                    if not folders:
                        raise ValueError(
                            "No archived reports found"
                        )

                    folder = folders[0]

                integrity = verify_report(folder)

                self.app.call_from_thread(
                    self.display_integrity,
                    integrity,
                )

                status = (
                    "REPORT INTEGRITY VERIFIED"
                    if integrity["passed"]
                    else "REPORT INTEGRITY FAILURE"
                )

        except Exception as exc:

            status = "OPERATION FAILED"

            self.app.call_from_thread(
                self.write,
                f"[FAIL] {type(exc).__name__}: {exc}",
                "#ff7777",
            )

            self.app.call_from_thread(
                self.clear_metrics,
            )

        finally:

            self.app.call_from_thread(
                self.finish,
                status,
            )

    def clear_metrics(self):

        for key, label in (
            ("local", "LOCAL CHECKS"),
            ("integrity", "INTEGRITY"),
            ("release", "RELEASE"),
        ):

            self.query_one(
                f"#report-{key}", Static
            ).update(f"{label}\n--")

    def display_integrity(self, integrity):

        for filename, passed in integrity["checks"].items():

            self.write(
                f"{filename}: "
                f"{'OK' if passed else 'FAILED'}",
                "#40dfb7" if passed else "#ff7777",
            )

        self.query_one(
            "#report-integrity", Static
        ).update(
            "INTEGRITY\n"
            + (
                "VERIFIED"
                if integrity["passed"]
                else "FAILED"
            )
        )

    def display_report(self, result):

        data = result["data"]

        release = data["release"]

        self.current_report = Path(
            result["directory"]
        )

        self.query_one(
            "#report-local", Static
        ).update(
            "LOCAL CHECKS\n"
            + release["local_status"]
        )

        self.query_one(
            "#report-release", Static
        ).update(
            "RELEASE\n"
            + release["release_status"]
        )

        self.write("")
        self.write("=" * 65, "#40dfb7")
        self.write(
            "INFRASTRUCTURE ENGINEERING REPORT",
            "#40dfb7",
        )
        self.write("=" * 65, "#40dfb7")
        self.write(f"Generated: {data['timestamp']}")

        self.write("")
        self.write(
            "EXECUTIVE ASSESSMENT",
            "#40dfb7",
        )

        self.write(
            f"Local verification: {release['local_status']}"
        )

        self.write(
            f"Release status: {release['release_status']}"
        )

        self.write(release["reason"], "#e5bb72")

        system = data["system"]

        self.write("")
        self.write("SYSTEM INFRASTRUCTURE", "#40dfb7")

        for key, value in system.items():
            self.write(f"{key}: {value}")

        self.write("")
        self.write("OPERATIONAL VERIFICATION", "#40dfb7")

        checks = {
            "Application online":
                data["application"].get("online"),
            "Security audit":
                data["security"]["passed"],
            "Acceptance tests":
                data["acceptance"]["passed"],
        }

        for label, passed in checks.items():

            self.write(
                f"{label}: "
                f"{'PASS' if passed else 'FAIL'}",
                "#40dfb7" if passed else "#ff7777",
            )

        self.write("")
        self.write("INCIDENT EVIDENCE", "#40dfb7")

        for key in (
            "total",
            "detected",
            "recovered",
            "recovery_rate",
            "invalid_records",
        ):

            self.write(
                f"{key}: {data['incidents'][key]}"
            )

        self.write("")
        self.write("BACKUP INVENTORY", "#40dfb7")

        self.write(
            f"Archives: "
            f"{data['backups']['archive_count']}"
        )

        self.write("")
        self.write("CI/CD INTELLIGENCE", "#40dfb7")

        pipeline = data["pipeline"]

        if pipeline.get("available"):

            summary = pipeline["summary"]

            for key in (
                "total",
                "successful",
                "failed",
                "success_rate",
                "exact_commit_success",
            ):

                self.write(
                    f"{key}: {summary[key]}"
                )

        else:

            self.write(
                "Remote pipeline unavailable",
                "#e5bb72",
            )

        self.write("")
        self.write("EXPORTED ARTIFACTS", "#40dfb7")
        self.write(str(self.current_report))

        self.display_integrity(
            result["integrity"]
        )

    def finish(self, status):

        self.running = False

        self.query_one(
            "#report-status", Static
        ).update(status)

        for button in self.query(Button):
            button.disabled = False

    @on(Button.Pressed, "#report-return")
    def return_pressed(self):
        self.action_back()

    def action_back(self):

        if self.running:
            self.notify(
                "Wait for report operation to finish."
            )
            return

        self.app.pop_screen()
