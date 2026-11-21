"""Read-only GitHub Actions intelligence workspace."""

from rich.text import Text

from textual import on, work
from textual.screen import Screen
from textual.containers import Horizontal
from textual.widgets import (
    Header,
    Footer,
    Static,
    Button,
    DataTable,
    RichLog,
)

from nexus_ui.services.pipeline import pipeline_snapshot


class PipelineScreen(Screen):

    BINDINGS = [
        ("f5", "refresh_pipeline", "Refresh"),
        ("escape", "back", "Return"),
    ]

    DEFAULT_CSS = """
    PipelineScreen {
        background: #080f17;
        color: #d7e6ed;
    }

    #pipeline-title {
        height: 3;
        padding: 1 2;
        background: #101d29;
        color: #40dfb7;
        text-style: bold;
    }

    #pipeline-metrics {
        height: 5;
        padding: 0 1;
    }

    .pipeline-metric {
        width: 1fr;
        height: 5;
        border: round #245d5d;
        content-align: center middle;
        color: #40dfb7;
        text-style: bold;
    }

    #pipeline-details {
        height: 12;
        border: round #245d5d;
        margin: 1 1 0 1;
        padding: 0 1;
    }

    #pipeline-history {
        height: 1fr;
        margin: 1;
        border: round #245d5d;
        background: #080f17;
    }

    #pipeline-status {
        height: 2;
        padding: 0 2;
        color: #40dfb7;
    }

    #pipeline-controls {
        height: 3;
        padding: 0 1;
    }

    #pipeline-controls Button {
        margin-right: 2;
    }
    """

    def __init__(self):
        super().__init__()
        self.running = False
        self.snapshot = None

    def compose(self):

        yield Header()

        yield Static(
            "NEXUS / CI/CD PIPELINE INTELLIGENCE",
            id="pipeline-title",
        )

        with Horizontal(id="pipeline-metrics"):

            for key, label in (
                ("success", "SUCCESSFUL"),
                ("failed", "FAILED"),
                ("rate", "SUCCESS RATE"),
                ("duration", "AVG DURATION"),
            ):

                yield Static(
                    f"{label}\n--",
                    id=f"pipeline-{key}",
                    classes="pipeline-metric",
                )

        yield RichLog(
            id="pipeline-details",
            wrap=True,
            markup=False,
        )

        yield DataTable(
            id="pipeline-history",
            cursor_type="row",
            zebra_stripes=True,
        )

        yield Static(
            "CONNECTING TO GITHUB ACTIONS",
            id="pipeline-status",
        )

        with Horizontal(id="pipeline-controls"):

            yield Button(
                "Refresh Pipeline",
                id="pipeline-refresh",
                variant="success",
            )

            yield Button(
                "Return",
                id="pipeline-return",
            )

        yield Footer()

    def on_mount(self):

        table = self.query_one(
            "#pipeline-history", DataTable
        )

        table.add_columns(
            "RUN ID",
            "WORKFLOW",
            "BRANCH",
            "COMMIT",
            "RESULT",
            "DURATION",
        )

        self.action_refresh_pipeline()

    def action_refresh_pipeline(self):

        if self.running:
            return

        self.running = True

        self.query_one(
            "#pipeline-refresh", Button
        ).disabled = True

        self.query_one(
            "#pipeline-status", Static
        ).update("RETRIEVING LIVE PIPELINE DATA")

        self.load_pipeline()

    @work(thread=True, exclusive=True)
    def load_pipeline(self):

        try:

            data = pipeline_snapshot()

            self.app.call_from_thread(
                self.render_snapshot,
                data,
            )

        except Exception:

            self.app.call_from_thread(
                self.render_error,
                "Pipeline retrieval failed. "
                "Check GitHub CLI and repository access.",
            )

    def render_error(self, message):

        self.snapshot = None

        self.query_one(
            "#pipeline-history", DataTable
        ).clear()

        for key, label in (
            ("success", "SUCCESSFUL"),
            ("failed", "FAILED"),
            ("rate", "SUCCESS RATE"),
            ("duration", "AVG DURATION"),
        ):

            self.query_one(
                f"#pipeline-{key}", Static
            ).update(f"{label}\n--")

        log = self.query_one(
            "#pipeline-details", RichLog
        )

        log.clear()

        log.write(
            Text(message, style="#ff7777")
        )

        self.finish("PIPELINE DATA UNAVAILABLE")

    def render_snapshot(self, data):

        if not data["available"]:

            self.render_error(
                "GitHub Actions data unavailable. "
                "Check network and authentication."
            )

            return

        self.snapshot = data

        local = data["local"]
        summary = data["summary"]

        rate = summary["success_rate"]
        duration = summary["average_duration_seconds"]

        metrics = {
            "success": (
                "SUCCESSFUL",
                summary["successful"],
            ),
            "failed": (
                "FAILED",
                summary["failed"],
            ),
            "rate": (
                "SUCCESS RATE",
                f"{rate}%" if rate is not None else "--",
            ),
            "duration": (
                "AVG DURATION",
                f"{duration}s" if duration is not None else "--",
            ),
        }

        for key, (label, value) in metrics.items():

            self.query_one(
                f"#pipeline-{key}", Static
            ).update(f"{label}\n{value}")

        log = self.query_one(
            "#pipeline-details", RichLog
        )

        log.clear()

        log.write(Text(
            "REPOSITORY INTELLIGENCE",
            style="#40dfb7",
        ))

        remote = data["remote_main"]

        details = [
            f"Repository : {local['repository']}",
            f"Branch     : {local['branch']}",
            f"Local HEAD : {local['commit']}",
            f"Remote main: {remote or 'Unavailable'}",
            "Working tree: " + (
                "UNCOMMITTED CHANGES"
                if local["dirty"]
                else "CLEAN"
            ),
            f"Recent runs: {summary['total']} "
            f"| Active: {summary['active']}",
        ]

        for line in details:
            log.write(Text(line))

        if summary["exact_commit_success"]:

            log.write(Text(
                "Committed HEAD has a successful historical run.",
                style="#40dfb7",
            ))

        else:

            log.write(Text(
                "No successful exact-commit run found "
                "in retrieved history.",
                style="#e5bb72",
            ))

        if local["dirty"]:

            log.write(Text(
                "WARNING: Uncommitted changes are not CI-certified.",
                style="#e5bb72",
            ))

        table = self.query_one(
            "#pipeline-history", DataTable
        )

        table.clear()

        for run in data["runs"]:

            status = (
                run["conclusion"]
                or run["status"]
            ).upper()

            color = (
                "#40dfb7" if status == "SUCCESS"
                else "#ff7777" if status == "FAILURE"
                else "#e5bb72"
            )

            seconds = run["duration_seconds"]

            table.add_row(
                str(run["id"]),
                Text(run["workflow"]),
                Text(run["branch"]),
                run["commit"][:12],
                Text(status, style=color),
                f"{seconds}s"
                if seconds is not None
                else "--",
            )

        self.finish(
            f"LIVE DATA / {summary['total']} RECENT RUNS "
            f"/ {data['timestamp']}"
        )

    def finish(self, status):

        self.running = False

        self.query_one(
            "#pipeline-status", Static
        ).update(status)

        self.query_one(
            "#pipeline-refresh", Button
        ).disabled = False

    @on(Button.Pressed, "#pipeline-refresh")
    def refresh_pressed(self):

        self.action_refresh_pipeline()

    @on(Button.Pressed, "#pipeline-return")
    def return_pressed(self):

        self.action_back()

    def action_back(self):

        if self.running:
            self.notify("Wait for pipeline refresh.")
            return

        self.app.pop_screen()
