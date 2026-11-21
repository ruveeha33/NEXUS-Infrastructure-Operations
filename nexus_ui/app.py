import asyncio
import subprocess
from collections import deque
from datetime import datetime

from rich.text import Text
from nexus_ui.screens.inspector import Inspector
from nexus_ui.screens.control import ServiceControl
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import (
    Horizontal,
    Vertical,
    VerticalScroll,
)
from textual.widgets import (
    Button,
    Footer,
    Static,
    Sparkline,
    RichLog,
)
from textual import work

from nexus_ui.services.telemetry import (
    ROOT,
    snapshot,
    http_health,
    log_snapshot,
    process_snapshot,
)

OPERATIONS = {
    "monitor": "Operations monitoring",
    "audit": "Security audit",
    "backup": "Create verified backup",
    "recover": "Isolated disaster recovery",
    "verify": "Acceptance test suite",
    "status": "Application status",
}


class ResourceGraph(Static):
    """Fixed-scale resource history: each column spans 0-100%."""

    def on_mount(self):
        self.samples = []

    def set_samples(self, samples):
        self.samples = list(samples)
        self.draw_graph()

    def on_resize(self):
        if hasattr(self, "samples"):
            self.draw_graph()

    def draw_graph(self):
        width = max(1, self.size.width - 6)
        samples = self.samples[-width:]
        samples = [None] * (width - len(samples)) + samples
        levels = " ▁▂▃▄▅▆▇█"

        result = Text()

        for row, threshold in enumerate((75, 50, 25, 0)):
            label = ("100%", " 75%", " 50%", " 25%")[row]
            result.append(label + " ", style="#60758b")

            for value in samples:
                if value is None:
                    result.append("·", style="#233545")
                    continue

                fraction = max(
                    0, min(1, (value - threshold) / 25)
                )

                level = min(8, round(fraction * 8))

                result.append(
                    levels[level] if level else "·",
                    style="#50dfb7" if level else "#233545",
                )

            if row != 3:
                result.append("\n")

        self.update(result)


from nexus_ui.widgets.compact_graph import CompactGraph

class Nexus(App):
    TITLE = "NEXUS"
    SUB_TITLE = "DecodeLabs Infrastructure Operations"


    CSS = 'Screen {\n    background: #0b141e;\n    color: #d9e7ef;\n}\n\nHeader {\n    background: #162735;\n    color: #59dfc4;\n    text-style: bold;\n}\n\nFooter {\n    background: #111e29;\n    color: #819eaf;\n}\n\nFooterKey {\n    background: #111e29;\n    color: #b8cedb;\n}\n\nButton {\n    background: #1b303e;\n    color: #c6dbe6;\n    border: none;\n    text-style: none;\n    min-width: 8;\n}\n\nButton:hover {\n    background: #25424b;\n    color: #59dfc4;\n}\n\nButton:focus {\n    background: #20443f;\n    color: #59dfc4;\n    text-style: bold;\n}\n\nButton.-success {\n    background: #20443f;\n    color: #59dfc4;\n}\n\nButton.-warning {\n    background: #493c25;\n    color: #e4bb78;\n}\n\nButton.-error {\n    background: #492a32;\n    color: #ff9292;\n}\n\nButton:disabled {\n    background: #14212b;\n    color: #526b7b;\n}\n\nInput {\n    background: #101e29;\n    color: #d9e7ef;\n    border: tall #304856;\n}\n\nInput:focus {\n    border: tall #59dfc4;\n    background: #142633;\n}\n\nInput > .input--placeholder {\n    color: #718c9c;\n}\n\nRichLog {\n    background: #101e29;\n    color: #d9e7ef;\n    scrollbar-color: #385665;\n    scrollbar-background: #101e29;\n}\n\nDataTable {\n    background: #101e29;\n    color: #d9e7ef;\n    scrollbar-color: #385665;\n    scrollbar-background: #101e29;\n}\n\nDataTable > .datatable--header {\n    background: #1b303e;\n    color: #59dfc4;\n    text-style: bold;\n}\n\nDataTable > .datatable--cursor {\n    background: #20443f;\n    color: #e4edf3;\n}\n\nDataTable > .datatable--odd-row {\n    background: #12222e;\n}\n\nDataTable > .datatable--even-row {\n    background: #101e29;\n}\n\nListView {\n    background: #101e29;\n    color: #b8cedb;\n}\n\nListItem {\n    background: #101e29;\n    color: #b8cedb;\n}\n\nListItem.-highlight {\n    background: #20443f;\n    color: #59dfc4;\n}\n\nVerticalScroll {\n    scrollbar-size-vertical: 1;\n    scrollbar-color: #385665;\n    scrollbar-background: #101e29;\n}\n\nHorizontalScroll {\n    scrollbar-color: #385665;\n    scrollbar-background: #101e29;\n}\n\nModalScreen {\n    background: #071018 70%;\n}\n\nLoadingIndicator {\n    background: #101e29;\n    color: #59dfc4;\n}\n\n#navigation Button {\n    min-width: 0;\n    height: 1;\n    margin: 0;\n    padding: 0 1;\n    background: #111e29;\n    color: #b8cedb;\n    content-align: left middle;\n    text-align: left;\n}\n\n#navigation Button:hover {\n    background: #25424b;\n    color: #59dfc4;\n}\n\n#navigation Button.selected {\n    background: #20443f;\n    color: #59dfc4;\n    text-style: bold;\n}\n\n\nScreen {\n    background: #0b141e;\n    color: #d9e7ef;\n}\n\n#nexus-brand {\n    height: 3;\n    padding: 1 2;\n    background: #162735;\n    color: #59dfc4;\n    text-style: bold;\n}\n\n#nexus-layout {\n    height: 1fr;\n}\n\n#navigation {\n    width: 29;\n    height: 100%;\n    background: #111e29;\n    border-right: solid #304856;\n    padding: 0 1;\n    scrollbar-size-vertical: 1;\n    scrollbar-color: #304856;\n}\n\n.navigation-group {\n    height: 2;\n    padding: 1 1 0 1;\n    color: #819eaf;\n    text-style: bold;\n}\n\n#navigation Button {\n    width: 100%;\n    min-width: 0;\n    height: 1;\n    margin: 0;\n    padding: 0 1;\n    background: #111e29;\n    color: #b8cedb;\n    border: none;\n    content-align: left middle;\n    text-align: left;\n    text-style: none;\n}\n\n#navigation Button:hover {\n    background: #25424b;\n    color: #59dfc4;\n}\n\n#navigation Button.selected {\n    background: #20443f;\n    color: #59dfc4;\n    text-style: bold;\n}\n\n#nav-footer {\n    height: 3;\n    padding: 1;\n    color: #819eaf;\n}\n\n#content {\n    width: 1fr;\n    height: 100%;\n    padding: 0 1;\n}\n\n#workspace {\n    height: 1fr;\n}\n\n#overview {\n    width: 2fr;\n    height: 100%;\n    padding: 0 1;\n    scrollbar-size-vertical: 1;\n}\n\n#intelligence {\n    width: 1fr;\n    height: 100%;\n    padding: 0 1;\n    scrollbar-size-vertical: 1;\n}\n\n#overview-heading {\n    height: 3;\n    padding: 1 0;\n    color: #e4edf3;\n    text-style: bold;\n}\n\n#health {\n    height: 5;\n    padding: 1 2;\n    background: #142b31;\n    border: round #345a5b;\n    margin-bottom: 1;\n}\n\n#resource-title {\n    height: 2;\n    color: #819eaf;\n    text-style: bold;\n}\n\n.metric {\n    height: 5;\n    margin-bottom: 1;\n    background: #162633;\n    border: round #304856;\n    padding: 0 1;\n}\n\n.metric-label {\n    height: 1;\n    color: #d9e7ef;\n    text-style: bold;\n}\n\nCompactGraph {\n    height: 2;\n    background: #162633;\n}\n\n#report {\n    height: auto;\n    min-height: 7;\n    padding: 1;\n    background: #142330;\n    border: round #304856;\n}\n\n#system {\n    height: auto;\n    min-height: 9;\n    margin: 0 0 1 0;\n    padding: 0 1;\n    background: #162633;\n    border: round #304856;\n}\n\n#traffic {\n    height: auto;\n    min-height: 8;\n    margin-bottom: 1;\n    padding: 0 1;\n    background: #162633;\n    border: round #304856;\n}\n\n#processes {\n    height: auto;\n    min-height: 11;\n    margin-bottom: 1;\n    padding: 0 1;\n    background: #162633;\n    border: round #304856;\n}\n\n#assurance {\n    height: auto;\n    min-height: 6;\n    padding: 0 1;\n    background: #142b31;\n    border: round #345a5b;\n    color: #b8cedb;\n}\n\n#operations {\n    height: 9;\n    display: none;\n    padding: 1;\n    background: #162633;\n}\n\n#operations Horizontal {\n    height: 3;\n}\n\n#operations Button {\n    width: 1fr;\n    margin-right: 1;\n    background: #20443f;\n    border: none;\n    color: #59dfc4;\n}\n\n#output {\n    height: 1fr;\n    padding: 1;\n    background: #0b141e;\n    border: round #304856;\n}\n\n#statusbar {\n    height: 1;\n    background: #162735;\n    color: #59dfc4;\n}\n\n#nexus-shortcuts {\n    height: 1;\n    background: #111e29;\n    color: #819eaf;\n}\n\nFooter {\n    background: #111e29;\n    color: #819eaf;\n}\n'


    BINDINGS = [
        ("r", "reports", "Reports"),
        ("c", "pipeline", "CI/CD"),
        ("i", "incidents", "Incidents"),
        ("h", "ssh_lab", "SSH Lab"),
        ("f", "fhs", "Linux FHS"),
        ("a", "academy", "Academy"),
        ("m", "mastery", "Linux Lab"),
        Binding("1", "show_overview", "Overview"),
        Binding("2", "show_operations", "Operations"),
        Binding("3", "show_logs", "Logs"),
        Binding("4", "run_operation('audit')", "Audit"),
        Binding("5", "run_operation('backup')", "Backup"),
        Binding("6", "run_operation('recover')", "Recovery"),
        Binding("7", "run_operation('verify')", "Verify"),
        Binding("8", "inspect('processes')", "Processes"),
        Binding("9", "inspect('filesystem')", "Files"),
        Binding("n", "inspect('network')", "Network"),
        Binding("g", "inspect('repository')", "Git"),
        Binding("s", "service_control", "Services"),
        Binding("q", "safe_quit", "Exit"),
    ]

    def __init__(self):
        super().__init__()
        self.history = {
            "cpu": deque(maxlen=80),
            "memory": deque(maxlen=80),
            "disk": deque(maxlen=80),
        }
        self.busy = False
        self.refreshing = False
        self.current_view = "overview"



    def compose(self):
        yield Static(
            " ◈  N E X U S     /     DECODELABS"
            "     /     INFRASTRUCTURE ENGINEERING",
            id="nexus-brand",
        )

        with Horizontal(id="nexus-layout"):

            with VerticalScroll(id="navigation"):

                groups = (
                    ("COMMAND", (
                        ("1", "Overview", "overview"),
                        ("2", "Operations", "operations"),
                        ("S", "Service Control", "services"),
                    )),
                    ("OBSERVABILITY", (
                        ("3", "Event Stream", "logs"),
                        ("8", "Processes", "processes"),
                        ("N", "Network", "network"),
                        ("9", "Filesystem", "filesystem"),
                    )),
                    ("RESILIENCE", (
                        ("4", "Security Audit", "audit"),
                        ("5", "Create Backup", "backup"),
                        ("6", "Recovery", "recover"),
                        ("I", "Incident Center", "incidents"),
                    )),
                    ("ENGINEERING", (
                        ("G", "Repository", "repository"),
                        ("C", "CI/CD Pipeline", "pipeline"),
                        ("7", "Verification", "verify"),
                        ("R", "Reports", "reports"),
                    )),
                    ("LINUX ACADEMY", (
                        ("M", "Command Lab", "mastery"),
                        ("F", "Linux FHS", "fhs"),
                        ("A", "Academy", "academy"),
                        ("H", "SSH Lab", "ssh-lab"),
                    )),
                )

                for group, entries in groups:

                    yield Static(
                        group,
                        classes="navigation-group",
                    )

                    for key, label, ident in entries:

                        yield Button(
                            f"{key:>2}   {label}",
                            id=f"nav-{ident}",
                            classes=(
                                "selected"
                                if ident == "overview"
                                else ""
                            ),
                        )

                yield Static(
                    "LOCAL ENGINEERING NODE",
                    id="nav-footer",
                )

            with Vertical(id="content"):

                with Horizontal(id="workspace"):

                    with VerticalScroll(id="overview"):

                        yield Static(
                            "INFRASTRUCTURE OVERVIEW",
                            id="overview-heading",
                        )

                        yield Static(
                            "Checking application...",
                            id="health",
                        )

                        yield Static(
                            "RESOURCE TELEMETRY",
                            id="resource-title",
                        )

                        for metric in (
                            "cpu", "memory", "disk"
                        ):

                            with Vertical(classes="metric"):

                                yield Static(
                                    metric.upper(),
                                    id=f"{metric}-label",
                                    classes="metric-label",
                                )

                                yield CompactGraph(
                                    id=f"{metric}-graph"
                                )

                        yield Static(
                            "Waiting for application events...",
                            id="report",
                        )

                    with VerticalScroll(id="intelligence"):

                        yield Static(
                            "Collecting system details...",
                            id="system",
                        )

                        yield Static(
                            "Collecting traffic...",
                            id="traffic",
                        )

                        yield Static(
                            "Collecting processes...",
                            id="processes",
                        )

                        yield Static(
                            "ENGINEERING ASSURANCE\n\n"
                            "Open Reports [R] for verified evidence.\n"
                            "Open CI/CD [C] for pipeline status.",
                            id="assurance",
                        )

                with Vertical(id="operations"):

                    yield Static("ENGINEERING OPERATIONS")

                    with Horizontal():
                        yield Button("Monitor", id="op-monitor")
                        yield Button("Audit", id="op-audit")
                        yield Button("Backup", id="op-backup")

                    with Horizontal():
                        yield Button("Recover", id="op-recover")
                        yield Button("Verify", id="op-verify")
                        yield Button("Status", id="op-status")

                yield RichLog(
                    id="output",
                    wrap=True,
                    markup=False,
                    max_lines=2000,
                )

        yield Static(
            " LOCAL NODE | INITIALIZING",
            id="statusbar",
        )

        yield Static(
            "  Scroll navigation for all workspaces"
            "  |  Q Exit  |  Esc Return from workspace",
            id="nexus-shortcuts",
        )

    def on_mount(self):
        self.query_one("#output").display = False
        self.set_interval(5, self.refresh_data)
        self.refresh_data()

    @work(exclusive=True, group="telemetry")
    async def refresh_data(self):
        data, counts_logs, health, processes = (
            await asyncio.gather(
                asyncio.to_thread(snapshot),
                asyncio.to_thread(log_snapshot),
                asyncio.to_thread(http_health),
                asyncio.to_thread(process_snapshot),
            )
        )

        counts, logs = counts_logs


        for name in ("cpu", "memory", "disk"):

            value = data[name]

            self.history[name].append(value)

            self.query_one(
                f"#{name}-graph", CompactGraph
            ).set_samples(self.history[name])

            label = {
                "cpu": "CPU UTILIZATION",
                "memory": "MEMORY UTILIZATION",
                "disk": "STORAGE UTILIZATION",
            }[name]

            filled = max(
                0,
                min(16, round(value / 100 * 16))
            )

            color = {
                "cpu": "#59dfc4",
                "memory": "#83b8eb",
                "disk": "#b6a5e4",
            }[name]

            metric = Text(
                f"{label:<20} {value:5.1f}%  ",
                style=color,
            )

            metric.append(
                "━" * filled,
                style=color,
            )

            metric.append(
                "─" * (16 - filled),
                style="#38505e",
            )

            self.query_one(
                f"#{name}-label", Static
            ).update(metric)

        state = (
            "● OPERATIONAL"
            if health["online"]
            else "● UNAVAILABLE"
        )

        latency = (
            f"{health['latency']} ms"
            if health["latency"] is not None
            else "N/A"
        )

        status = (
            str(health["status"])
            if health["status"] is not None
            else "N/A"
        )

        self.query_one("#health", Static).update(
            Text(
                f"APPLICATION / {state}\n"
                f"127.0.0.1:8095  |  HTTP {status}"
                f"  |  {latency}",
                style="#59dfc4"
                if health["online"]
                else "#ff7777",
            )
        )

        uptime = data["uptime"]
        hours, remainder = divmod(uptime, 3600)
        minutes = remainder // 60

        self.query_one("#system", Static).update(
            Text(
                "SYSTEM INTELLIGENCE\n"
                f"Node      {data['host']}\n"
                f"Cores     {data['cores']}\n"
                f"Memory    {data['memory_used']:.1f} / "
                f"{data['memory_total']:.1f} GiB\n"
                f"Uptime    {hours}h {minutes}m\n"
                f"Processes {data['processes']}",
                style="#b8cadb",
            )
        )

        traffic = Text(
            "HTTP TRAFFIC / LOG SAMPLE\n",
            style="#819eaf",
        )

        for code, color in (
            ("200", "#59dfc4"),
            ("304", "#6caaff"),
            ("404", "#e6b45c"),
        ):
            traffic.append(
                f"{code}    {counts[code]:>6}\n",
                style=color,
            )

        traffic.append(
            f"\nTOTAL  "
            f"{sum(v for k, v in counts.items() if k != 'probe'):>6}"
            f"\nPROBES {counts['probe']:>6}"
        )

        self.query_one(
            "#traffic", Static
        ).update(traffic)

        table = Text(
            "TOP PROCESSES / MEMORY\n",
            style="#819eaf",
        )

        for proc in processes[:5]:
            name = (proc.get("name") or "?")[:14]
            memory = proc.get("memory_percent") or 0

            table.append(
                f"{proc['pid']:>6} "
                f"{name:<14} {memory:5.1f}%\n",
                style="#c4d3e3",
            )

        self.query_one(
            "#processes", Static
        ).update(table)

        recent = Text(
            "APPLICATION EVENTS / PROBES EXCLUDED\n\n",
            style="#819eaf",
        )

        visible_logs = [
            line for line in logs
            if "?probe=nexus" not in line
        ]

        if not visible_logs:
            recent.append(
                "No non-probe events in recent log sample.\n",
                style="#819eaf",
            )

        for line in visible_logs[-5:]:
            recent.append(
                line + "\n",
                style="#e6b45c"
                if " 404 " in line
                else "#8fb7c8",
            )

        self.query_one(
            "#report", Static
        ).update(recent)

        if self.current_view == "logs":
            output = self.query_one("#output", RichLog)
            output.clear()

            for line in logs:
                output.write(Text(line))

        operation_state = (
            "OPERATION RUNNING"
            if self.busy
            else "READY"
        )

        self.query_one("#statusbar", Static).update(
            f" LOCAL NODE  |  {operation_state}"
            f"  |  {data['time']}"
        )

    def select_navigation(self, view):
        for button in self.query("#navigation Button"):
            button.set_class(
                button.id == f"nav-{view}", "selected"
            )

    def action_show_overview(self):
        self.current_view = "overview"
        self.select_navigation("overview")
        self.query_one("#workspace").display = True
        self.query_one("#operations").display = False
        self.query_one("#output").display = False

    def action_show_operations(self):
        self.current_view = "operations"
        self.select_navigation("operations")
        self.query_one("#workspace").display = False
        self.query_one("#operations").display = True
        self.query_one("#output").display = True

    def action_show_logs(self):
        if self.busy:
            self.notify(
                "Wait for current operation.",
                severity="warning",
            )
            return

        self.current_view = "logs"
        self.select_navigation("logs")
        self.query_one("#workspace").display = False
        self.query_one("#operations").display = False
        self.query_one("#output").display = True

        output = self.query_one("#output", RichLog)
        output.clear()
        output.write("Collecting live application logs...")

    def action_safe_quit(self):
        if self.busy or getattr(self.screen, "busy", False):
            self.notify("Wait for current operation.")
            return
        self.exit()

    def action_service_control(self):
        if self.busy:
            self.notify("Wait for current operation.")
            return
        if not isinstance(self.screen, ServiceControl):
            self.push_screen(ServiceControl())

    def action_inspect(self, mode):
        if self.busy:
            self.notify(
                "Wait for the current operation.",
                severity="warning",
            )
            return

        self.push_screen(Inspector(mode))

    def on_button_pressed(self, event):
        button_id = event.button.id or ""

        if button_id == "nav-overview":
            self.action_show_overview()
        elif button_id == "nav-operations":
            self.action_show_operations()
        elif button_id == "nav-logs":
            self.action_show_logs()
        elif button_id in (
            "nav-processes",
            "nav-filesystem",
            "nav-network",
            "nav-repository",
        ):
            self.action_inspect(button_id[4:])
        elif button_id == "nav-incidents":
            self.action_incidents()
        elif button_id == "nav-pipeline":
            self.action_pipeline()
        elif button_id == "nav-reports":
            self.action_reports()
        elif button_id == "nav-mastery":
            self.action_mastery()
        elif button_id == "nav-fhs":
            self.action_fhs()
        elif button_id == "nav-academy":
            self.action_academy()
        elif button_id == "nav-ssh-lab":
            self.action_ssh_lab()
        elif button_id == "nav-services":
            self.action_service_control()
        elif button_id.startswith("nav-"):
            self.action_run_operation(
                button_id[4:]
            )
        elif button_id.startswith("op-"):
            self.action_run_operation(
                button_id[3:]
            )

    def action_run_operation(self, operation):
        if operation not in OPERATIONS:
            return

        if self.busy:
            self.notify(
                "An operation is already running.",
                severity="warning",
            )
            return

        self.busy = True
        self.action_show_operations()
        self.execute_operation(operation)

    @work(exclusive=False, group="operations")
    async def execute_operation(self, operation):
        output = self.query_one("#output", RichLog)
        output.clear()

        output.write(
            Text(
                f"NEXUS / {OPERATIONS[operation]}\n"
                f"{datetime.now().isoformat()}\n",
                style="#59dfc4",
            )
        )

        try:
            result = await asyncio.to_thread(
                subprocess.run,
                [
                    str(ROOT / "scripts/ops.sh"),
                    operation,
                ],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=120,
            )

            for line in result.stdout.splitlines():
                color = "#b8cadb"

                if "[PASS]" in line:
                    color = "#59dfc4"
                elif "[FAIL]" in line:
                    color = "#ff7777"

                output.write(
                    Text(line, style=color)
                )

            success = result.returncode == 0

            output.write(
                Text(
                    "\nOPERATION COMPLETE"
                    if success
                    else f"\nEXIT CODE: {result.returncode}",
                    style="#59dfc4"
                    if success
                    else "#ff7777",
                )
            )

        except subprocess.TimeoutExpired:
            output.write(
                Text(
                    "Operation timed out.",
                    style="#ff7777",
                )
            )
        except Exception as exc:
            output.write(
                Text(
                    f"Operation error: {exc}",
                    style="#ff7777",
                )
            )
        finally:
            self.busy = False

    def action_mastery(self):
        if getattr(self, "busy", False):
            self.notify("An operation is currently running.")
            return

        from nexus_ui.screens.mastery import MasteryScreen

        self.push_screen(MasteryScreen())

    def action_fhs(self):
        if getattr(self, "busy", False):
            self.notify("An operation is currently running.")
            return

        from nexus_ui.screens.knowledge import KnowledgeScreen

        self.push_screen(KnowledgeScreen("filesystem"))

    def action_academy(self):
        if getattr(self, "busy", False):
            self.notify("An operation is currently running.")
            return

        from nexus_ui.screens.knowledge import KnowledgeScreen

        self.push_screen(KnowledgeScreen("academy"))

    def action_ssh_lab(self):
        if getattr(self, "busy", False):
            self.notify("An operation is currently running.")
            return

        from nexus_ui.screens.ssh_lab import SSHLabScreen

        self.push_screen(SSHLabScreen())

    def action_incidents(self):
        if getattr(self, "busy", False):
            self.notify("An operation is currently running.")
            return

        from nexus_ui.screens.incidents import IncidentScreen

        self.push_screen(IncidentScreen())

    def action_pipeline(self):
        if getattr(self, "busy", False):
            self.notify("An operation is currently running.")
            return

        from nexus_ui.screens.pipeline import PipelineScreen

        self.push_screen(PipelineScreen())

    def action_reports(self):
        if getattr(self, "busy", False):
            self.notify("An operation is currently running.")
            return

        from nexus_ui.screens.reports import ReportsScreen

        self.push_screen(ReportsScreen())


if __name__ == "__main__":
    Nexus().run()
