"""Interactive incident response command center."""

from rich.text import Text

from textual import on, work
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Header,
    Footer,
    Static,
    Button,
    ListView,
    ListItem,
    Label,
    RichLog,
)

from nexus_ui.services.incidents import (
    SCENARIOS,
    run_incident,
)


class IncidentScreen(Screen):

    BINDINGS = [
        ("escape", "back", "Return"),
    ]

    DEFAULT_CSS = """
    IncidentScreen {
        background: #080f17;
        color: #d7e6ed;
    }

    #incident-title {
        height: 3;
        padding: 1 2;
        background: #101d29;
        color: #40dfb7;
        text-style: bold;
    }

    #incident-metrics {
        height: 5;
        padding: 0 1;
    }

    .incident-metric {
        width: 1fr;
        height: 5;
        border: round #245d5d;
        padding: 0 2;
        color: #40dfb7;
        content-align: center middle;
        text-style: bold;
    }

    #incident-body {
        height: 1fr;
        padding: 1;
    }

    #incident-left {
        width: 40;
        height: 1fr;
    }

    #incident-list {
        height: 1fr;
        border: round #245d5d;
        background: #101d29;
    }

    #incident-list ListItem {
        padding: 1;
    }

    #incident-list ListItem.-highlight {
        background: #153b36;
        color: #40dfb7;
    }

    #incident-transcript {
        width: 1fr;
        height: 1fr;
        margin-left: 1;
        border: round #245d5d;
        padding: 1 2;
        background: #080f17;
    }

    #incident-status {
        height: 3;
        padding: 1 2;
        color: #40dfb7;
    }

    #incident-controls {
        height: 3;
        padding: 0 1;
    }

    #incident-controls Button {
        margin-right: 2;
    }
    """

    def __init__(self):
        super().__init__()

        self.scenarios = list(SCENARIOS)
        self.running = False
        self.attempts = 0
        self.detected = 0
        self.recovered = 0

    def compose(self):

        yield Header()

        yield Static(
            "NEXUS / INCIDENT COMMAND CENTER",
            id="incident-title",
        )

        with Horizontal(id="incident-metrics"):

            yield Static(
                "DETECTED\n0",
                id="incident-detected",
                classes="incident-metric",
            )

            yield Static(
                "RECOVERED\n0",
                id="incident-recovered",
                classes="incident-metric",
            )

            yield Static(
                "SUCCESS RATE\n--",
                id="incident-rate",
                classes="incident-metric",
            )

        with Horizontal(id="incident-body"):

            with Vertical(id="incident-left"):

                yield ListView(
                    *[
                        ListItem(
                            Label(
                                f"{i:02d} / {title}",
                                markup=False,
                            )
                        )
                        for i, title in enumerate(
                            SCENARIOS.values(),
                            start=1,
                        )
                    ],
                    id="incident-list",
                )

            yield RichLog(
                id="incident-transcript",
                wrap=True,
                markup=False,
                max_lines=2000,
            )

        yield Static(
            "TRAINING MODE / READY",
            id="incident-status",
        )

        with Horizontal(id="incident-controls"):

            yield Button(
                "Run Selected",
                id="incident-run",
                variant="success",
            )

            yield Button(
                "Run All",
                id="incident-all",
                variant="primary",
            )

            yield Button(
                "Return",
                id="incident-return",
            )

        yield Footer()

    def on_mount(self):

        self.query_one(
            "#incident-list", ListView
        ).index = 0

        self.write("NEXUS INCIDENT RESPONSE LAB")
        self.write("")
        self.write("Five controlled infrastructure incidents.")
        self.write("Original application remains isolated.")
        self.write("Select a scenario to execute.")
        self.write("JSON evidence is recorded automatically.")

    def write(self, message):

        colors = {
            "[BASELINE]": "#78a9b7",
            "[INJECT]": "#e5bb72",
            "[DETECT]": "#ff9977",
            "[DIAGNOSE]": "#82b9e5",
            "[RECOVER]": "#40dfb7",
            "[VERIFY]": "#40dfb7",
            "[CLEANUP]": "#78a9b7",
            "[EVIDENCE]": "#78a9b7",
            "[PASS]": "#40dfb7",
            "[FAIL]": "#ff7777",
        }

        color = next(
            (
                value
                for prefix, value in colors.items()
                if message.startswith(prefix)
            ),
            "#d7e6ed",
        )

        self.query_one(
            "#incident-transcript", RichLog
        ).write(Text(message, style=color))

    def update_metrics(self):

        rate = (
            f"{100 * self.recovered / self.attempts:.0f}%"
            if self.attempts
            else "--"
        )

        self.query_one(
            "#incident-detected", Static
        ).update(f"DETECTED\n{self.detected}")

        self.query_one(
            "#incident-recovered", Static
        ).update(f"RECOVERED\n{self.recovered}")

        self.query_one(
            "#incident-rate", Static
        ).update(f"SUCCESS RATE\n{rate}")

    def begin(self, scenarios):

        if self.running:
            return

        self.running = True

        for button in self.query(Button):
            button.disabled = True

        self.query_one(
            "#incident-transcript", RichLog
        ).clear()

        self.query_one(
            "#incident-status", Static
        ).update("INCIDENT RESPONSE IN PROGRESS")

        self.execute_scenarios(scenarios)

    @on(Button.Pressed, "#incident-run")
    def run_selected(self):

        index = self.query_one(
            "#incident-list", ListView
        ).index

        if index is not None:
            self.begin([self.scenarios[index]])

    @on(Button.Pressed, "#incident-all")
    def run_all(self):

        self.begin(list(self.scenarios))

    @work(thread=True, exclusive=True)
    def execute_scenarios(self, scenarios):

        passed = 0

        try:

            for scenario in scenarios:

                self.app.call_from_thread(
                    self.write,
                    "\n" + "=" * 55,
                )

                self.app.call_from_thread(
                    self.write,
                    SCENARIOS[scenario].upper(),
                )

                try:

                    result = run_incident(
                        scenario,
                        emit=lambda line:
                            self.app.call_from_thread(
                                self.write,
                                line,
                            ),
                    )

                    success = (
                        result.detected
                        and result.recovered
                    )

                    self.app.call_from_thread(
                        self.record_result,
                        result.detected,
                        success,
                    )

                    if success:
                        passed += 1

                    self.app.call_from_thread(
                        self.write,
                        f"ROOT CAUSE: {result.root_cause}",
                    )

                    self.app.call_from_thread(
                        self.write,
                        f"DURATION: {result.duration_ms} ms",
                    )

                    self.app.call_from_thread(
                        self.write,
                        "[PASS] Incident recovered"
                        if success
                        else "[FAIL] Recovery incomplete",
                    )

                except Exception as exc:

                    self.app.call_from_thread(
                        self.record_result,
                        False,
                        False,
                    )

                    self.app.call_from_thread(
                        self.write,
                        f"[FAIL] {exc}",
                    )

        finally:

            self.app.call_from_thread(
                self.finish,
                passed,
                len(scenarios),
            )

    def record_result(self, detected, recovered):

        self.attempts += 1
        self.detected += int(detected)
        self.recovered += int(recovered)

        self.update_metrics()

    def finish(self, passed, total):

        self.running = False

        self.query_one(
            "#incident-status", Static
        ).update(
            f"{passed}/{total} RECOVERED / "
            "TRAINING SESSION COMPLETE"
        )

        for button in self.query(Button):
            button.disabled = False

    @on(Button.Pressed, "#incident-return")
    def return_pressed(self):

        self.action_back()

    def action_back(self):

        if self.running:
            self.notify(
                "Wait for incident recovery to complete."
            )
            return

        self.app.pop_screen()
