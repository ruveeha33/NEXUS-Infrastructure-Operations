<div align="center">

# NEXUS

### INFRASTRUCTURE OPERATIONS WORKSTATION

**Observe the system. Investigate the signal. Operate with intent. Verify the outcome.**

A terminal-native Linux engineering workstation that brings system intelligence, controlled service operations, incident exercises, CI/CD visibility, and verifiable evidence into one cohesive interface.

[![NEXUS CI](https://github.com/ruveeha33/NEXUS-Infrastructure-Operations/actions/workflows/nexus-ci.yml/badge.svg)](https://github.com/ruveeha33/NEXUS-Infrastructure-Operations/actions/workflows/nexus-ci.yml)
[![Linux verification](https://github.com/ruveeha33/NEXUS-Infrastructure-Operations/actions/workflows/verify.yml/badge.svg)](https://github.com/ruveeha33/NEXUS-Infrastructure-Operations/actions/workflows/verify.yml)
![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![UI](https://img.shields.io/badge/UI-Textual-132A38)
![OS](https://img.shields.io/badge/Ubuntu%20%7C%20WSL2-Local%20workstation-30363D?logo=ubuntu&logoColor=white)

[Explore capabilities](#the-workstation) · [Architecture](#how-it-works) · [Get started](#get-started) · [Verification](#quality--verification) · [Security](#safety--scope)

</div>

---

## Engineering operations, in one terminal

Linux operations are rarely one task. An engineer moves between process inspection, network visibility, service health, incident investigation, command-line work, and proof that an action achieved its intended result.

**NEXUS** unifies those activities in a keyboard-driven **Textual** interface, backed by Python services and a preserved Bash-based Linux operations lab. Its goal is not to replace production observability or orchestration platforms; it is to make practical infrastructure engineering **visible, repeatable, and explainable** in a local learning environment.

> **Design principle:** Distinguish what the system *observes*, what the lab *simulates*, what an operator *requests*, and what the evidence *verifies*.

## At a glance

| | |
| :--- | :--- |
| **Interface** | Python + Textual terminal UI with dedicated workspaces |
| **Signals** | Host telemetry, process, filesystem, and network inspection |
| **Operations** | Scoped management of the companion Linux Operations Lab service |
| **Investigation** | Incident exercises, CI/CD run inspection, and report generation |
| **Practice** | Linux knowledge, command exercises, and local SSH mission |
| **Assurance** | Automated regression tests and two GitHub Actions workflows |

## The workstation

| Workspace | What you can explore |
| :--- | :--- |
| **Infrastructure dashboard** | Live-oriented system telemetry and operational overview, including resource history visualizations |
| **System inspector** | Processes, filesystem metadata, network connections, interfaces, repository information, and commit history |
| **Operational control** | View the lab service's health and process ownership; explicitly confirm start, stop, and restart actions; inspect operation history and backups |
| **Incident intelligence** | Work through simulated operational incidents and inspect their findings |
| **Pipeline intelligence** | Read GitHub Actions workflow results, run history, outcomes, and durations; refresh on demand |
| **Engineering assurance** | Generate local engineering reports, review archived reports, and verify SHA-256 integrity |
| **Linux knowledge & mastery** | Explore Linux concepts and structured engineering exercises |
| **Restricted command lab** | Practice Linux commands within application-defined restrictions |
| **SSH engineering** | Run a local OpenSSH training mission using temporary keys and a managed server lifecycle |

The interface is complemented by Bash tools for monitoring, verification, backup, isolated recovery testing, and security auditing.

### A look inside

> **Screenshot slot:** A real terminal capture of the NEXUS dashboard will go here. The repository intentionally does not use a fabricated product screenshot.

For the best visual introduction, capture NEXUS running at a wide terminal size and add an image at `docs/images/nexus-dashboard.png`, then replace this note with:

```markdown
![NEXUS infrastructure dashboard](docs/images/nexus-dashboard.png)
```

## How it works

```text
                         ┌───────────────────────────┐
                         │     NEXUS / Textual       │
                         │  terminal workspaces      │
                         └─────────────┬─────────────┘
                                       │
                 ┌─────────────────────┼─────────────────────┐
                 │                     │                     │
       ┌─────────▼──────────┐ ┌────────▼─────────┐ ┌────────▼──────────┐
       │ Host intelligence  │ │ Operational lab  │ │ Engineering       │
       │ telemetry, process │ │ scoped service   │ │ evidence, reports │
       │ filesystem, network│ │ control, Bash    │ │ CI/CD, SSH mission│
       └────────────────────┘ └────────┬─────────┘ └───────────────────┘
                                      │
                            ┌─────────▼──────────┐
                            │ Local companion    │
                            │ web application    │
                            │ 127.0.0.1:8095     │
                            └────────────────────┘
```

**Separation of responsibilities**

- `nexus_ui/screens/` presents the workspaces and interactions.
- `nexus_ui/services/` collects data and implements supporting operations.
- `nexus_ui/themes/` and `nexus_ui/widgets/` define the terminal presentation.
- `scripts/` preserves the original Linux operations toolkit.
- `app/` contains the separate, local companion web application.
- `tests/nexus/` and `.github/workflows/` provide regression and CI checks.

See [Technical Architecture](docs/ARCHITECTURE.md) and [Linux Command Reference](docs/LINUX-COMMANDS.md).

## Get started

**Prerequisites:** Ubuntu Linux or Ubuntu under WSL2, Python **3.14** available as `python3.14`, Bash, Git, and a terminal with modern color support. Some exercises require local utilities such as OpenSSH; availability and permissions depend on the host environment.

### 1. Clone and prepare

```bash
git clone https://github.com/ruveeha33/NEXUS-Infrastructure-Operations.git
cd NEXUS-Infrastructure-Operations

bash scripts/setup.sh
python3.14 -m venv .venv-nexus
.venv-nexus/bin/python -m pip install -r requirements-nexus.txt
```

### 2. Launch NEXUS

```bash
./nexus
```

The launcher starts the Textual application from `.venv-nexus` and uses a local instance lock to prevent overlapping sessions.

### 3. Optional: run the companion web lab

```bash
bash scripts/ops.sh start
```

Open **http://127.0.0.1:8095/** locally. This web lab is a separate component; NEXUS itself is a terminal application.

### 4. Run the regression suite

```bash
.venv-nexus/bin/python -m pytest tests/nexus -q
```

## Quality & verification

The published baseline passed **71/71 local regression tests**. Both GitHub-hosted workflows also completed successfully after the README update at commit [`9744b81`](https://github.com/ruveeha33/NEXUS-Infrastructure-Operations/commit/9744b81).

| Workflow | Verification | Result |
| :--- | :--- | :--- |
| [NEXUS Infrastructure CI](https://github.com/ruveeha33/NEXUS-Infrastructure-Operations/actions/workflows/nexus-ci.yml) | Python 3.14 dependencies, compilation, launcher syntax, NEXUS regression suite, repository hygiene | **Passed** |
| [Linux Operations Verification](https://github.com/ruveeha33/NEXUS-Infrastructure-Operations/actions/workflows/verify.yml) | Original Linux lab verification workflow | **Passed** |

**Evidence:** [NEXUS CI run](https://github.com/ruveeha33/NEXUS-Infrastructure-Operations/actions/runs/44937976137) · [Linux verification run](https://github.com/ruveeha33/NEXUS-Infrastructure-Operations/actions/runs/44937976220)

CI success confirms that the automated checks passed in their tested environment. It does not establish production readiness or guarantee that every privileged local operation will work on every machine.

## Safety & scope

NEXUS is a **single-host educational and development workstation**. It is not a production control plane, a remote administration platform, or a security isolation boundary.

- **Observation vs. action:** Inspection and pipeline views are distinct from operations that change local lab state.
- **Scoped service control:** The operational control workspace targets the companion Linux Operations Lab service and requires confirmation for disruptive actions.
- **Command restrictions:** The Linux command lab applies application-defined restrictions; do not treat them as equivalent to OS-level sandboxing.
- **SSH practice:** The SSH mission uses a local training lifecycle; review host prerequisites and permissions before running it.
- **Local-only web service:** Do not expose the development HTTP server to the internet.
- **Private local artifacts:** Keep credentials, configuration, logs, evidence, and virtual environments outside Git.

Review [SECURITY.md](SECURITY.md) before using operational features.

## Repository map

```text
NEXUS-Infrastructure-Operations/
├── nexus                    # Terminal launcher
├── nexus_ui/
│   ├── app.py               # Workstation application
│   ├── screens/             # Operator workspaces
│   ├── services/            # Supporting engineering logic
│   ├── themes/              # Textual styling
│   └── widgets/             # Reusable UI elements
├── scripts/                 # Bash operations toolkit
├── app/                     # Companion local web lab
├── tests/nexus/             # Automated regression tests
├── docs/                    # Architecture and learning docs
├── .github/workflows/       # CI and Linux verification
├── requirements-nexus.txt   # Pinned Python dependencies
└── README.md
```

## Project lineage

NEXUS extends the **DecodeLabs Linux Operations Lab**. The original Bash operations toolkit and local web application are retained; NEXUS adds the interactive terminal workstation, Python service layer, learning and investigation workspaces, and dedicated regression tests.

This repository is presented as a practical Linux and DevOps engineering project. Its design emphasizes operator understanding, traceable outcomes, and reproducible local verification.

---

<div align="center">

**NEXUS** · *Observe. Investigate. Operate. Verify.*

[Repository](https://github.com/ruveeha33/NEXUS-Infrastructure-Operations) · [Actions](https://github.com/ruveeha33/NEXUS-Infrastructure-Operations/actions) · [Architecture](docs/ARCHITECTURE.md) · [Security](SECURITY.md)

</div>
