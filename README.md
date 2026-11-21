<div align="center">

# NEXUS

### Infrastructure Operations Workstation

**OBSERVE · INVESTIGATE · OPERATE · VERIFY**

An interactive Linux engineering workstation for infrastructure visibility, operational investigation, controlled practice, and evidence-driven verification.

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white) ![Textual](https://img.shields.io/badge/Interface-Textual-1C2634) ![Platform](https://img.shields.io/badge/Platform-Ubuntu%20%7C%20WSL2-555555?logo=ubuntu&logoColor=white) ![Tests](https://img.shields.io/badge/Local%20tests-71%20passed-238636) [![NEXUS CI](https://github.com/ruveeha33/NEXUS-Infrastructure-Operations/actions/workflows/nexus-ci.yml/badge.svg)](https://github.com/ruveeha33/NEXUS-Infrastructure-Operations/actions/workflows/nexus-ci.yml)

</div>

---

## Overview

**NEXUS** brings essential Linux infrastructure operations into a unified terminal-based interface. Built with **Python, Textual, Bash, and system telemetry**, it combines inspection, monitoring, operational exercises, incident analysis, and reporting in a single local workstation.

It is designed as a **hands-on engineering and learning environment**: an approachable way to explore operational workflows while retaining clear boundaries between observation, simulation, and actions on the local host.

> **Scope:** NEXUS is a local educational and development workstation—not a production infrastructure management platform or a remotely exposed administration service.

## What NEXUS Includes

| Workspace / capability | Purpose |
| --- | --- |
| **Infrastructure control** | Explore local operational and service-management workflows. |
| **System inspection** | Inspect processes, filesystem information, and network context. |
| **Telemetry** | Review system and infrastructure signals within the terminal interface. |
| **Incident workspace** | Investigate simulated incidents and related operational findings. |
| **Pipeline analysis** | Examine pipeline-oriented workflows and their results. |
| **Evidence and reports** | Generate and review operational reports and archived evidence. |
| **Linux knowledge and mastery** | Practice and reinforce foundational Linux engineering concepts. |
| **Restricted command lab** | Work with Linux commands inside the application's defined restrictions. |
| **SSH practice** | Explore local SSH learning scenarios. |
| **Operations toolkit** | Use supporting Bash scripts for setup, monitoring, verification, backup, recovery, and security checks. |

## Architecture

```text
NEXUS
├── Textual terminal interface       nexus_ui/app.py
│   ├── Workspaces                  nexus_ui/screens/
│   ├── Operational services        nexus_ui/services/
│   ├── Themes and visual elements  nexus_ui/themes/ + widgets/
│   └── Linux learning workflows
├── Bash operations toolkit         scripts/
├── Original local web application  app/
├── Automated regression tests      tests/nexus/
└── GitHub Actions verification     .github/workflows/
```

The **Textual UI** organizes operator-facing workflows; the **Python service modules** implement their supporting logic; and the **Bash scripts** retain the original Linux operations exercises. The companion web application is served locally and is separate from the terminal workstation.

For the underlying Linux lab architecture, see [Technical Architecture](docs/ARCHITECTURE.md). For foundational commands, see [Linux Commands](docs/LINUX-COMMANDS.md).

## Quick Start

### Requirements

- **Ubuntu Linux** or **Ubuntu on WSL2**
- **Python 3.14** available as `python3.14`
- **Bash** and **Git**

### Install

```bash
git clone https://github.com/ruveeha33/NEXUS-Infrastructure-Operations.git
cd NEXUS-Infrastructure-Operations

bash scripts/setup.sh
python3.14 -m venv .venv-nexus
.venv-nexus/bin/python -m pip install -r requirements-nexus.txt
```

### Launch the workstation

```bash
./nexus
```

The launcher expects the `.venv-nexus` environment, starts the Textual application, and uses a local instance lock to prevent overlapping sessions.

### Run the original web application

```bash
bash scripts/ops.sh start
```

Open **http://127.0.0.1:8095/** on the same machine. The development web server is intended for local use only.

## Testing and Verification

Run the NEXUS regression suite:

```bash
.venv-nexus/bin/python -m pytest tests/nexus -q
```

**Verified publication baseline:** 71 automated tests passed locally, and the [NEXUS Infrastructure CI workflow](https://github.com/ruveeha33/NEXUS-Infrastructure-Operations/actions/runs/44937454821) completed successfully for commit `f0b4869`.

GitHub Actions includes a dedicated **Python 3.14 NEXUS test workflow**, alongside the original Linux verification workflow. The NEXUS workflow checks source compilation, launcher syntax, regression tests, and repository hygiene.

[![NEXUS CI](https://github.com/ruveeha33/NEXUS-Infrastructure-Operations/actions/workflows/nexus-ci.yml/badge.svg)](https://github.com/ruveeha33/NEXUS-Infrastructure-Operations/actions/workflows/nexus-ci.yml)

## Security and Operational Boundaries

NEXUS is designed for **local educational use**. Its command-practice environment is restricted, but that should not be interpreted as a substitute for host-level isolation or security review. Review operational commands and their effects before running them on a machine containing important data.

- Do **not** expose the development HTTP server to the public internet.
- Keep local configuration, credentials, runtime logs, evidence, and virtual environments out of version control.
- Treat configuration files used by Bash tooling as **trusted local inputs**.
- Review permissions and operational scripts before use.

See [SECURITY.md](SECURITY.md) for additional project security guidance.

## Repository Guide

| Path | Contents |
| --- | --- |
| `nexus` | NEXUS launcher and single-instance protection |
| `nexus_ui/screens/` | Interactive terminal workspaces |
| `nexus_ui/services/` | Operational logic and telemetry services |
| `nexus_ui/themes/` | Textual styling |
| `scripts/` | Linux operations and verification scripts |
| `app/` | Original local web application |
| `tests/nexus/` | NEXUS automated regression tests |
| `docs/` | Technical documentation and lab evidence |
| `.github/workflows/` | Automated verification workflows |

## Project Background

NEXUS extends the **DecodeLabs Linux Operations Lab**, preserving its original Bash operations toolkit and companion web application while adding a terminal-based infrastructure workstation, supporting Python services, and dedicated automated tests.

The project demonstrates foundational Linux and DevOps engineering practices in a reproducible, local learning environment.

---

<div align="center">

**NEXUS — Observe. Investigate. Operate. Verify.**

[Source Code](https://github.com/ruveeha33/NEXUS-Infrastructure-Operations) · [CI Results](https://github.com/ruveeha33/NEXUS-Infrastructure-Operations/actions) · [Architecture](docs/ARCHITECTURE.md)

</div>
