# NEXUS
## Infrastructure Operations Workstation

**Observe. Investigate. Operate. Verify.**

NEXUS is an interactive Linux infrastructure operations
workstation built with Python, Textual, Bash and system telemetry.

## Features

- Infrastructure monitoring and telemetry
- Process, filesystem and network inspection
- Local service management
- Incident simulation and pipeline analysis
- Evidence reporting
- Restricted Linux Command Lab
- Linux learning workspaces
- Local SSH practice environment
- Backup, recovery and security auditing

## Requirements

Ubuntu Linux or WSL2, Python 3.14, Bash and Git.

## Installation

Run these commands from the project directory:

    bash scripts/setup.sh
    python3.14 -m venv .venv-nexus
    .venv-nexus/bin/python -m pip install -r requirements-nexus.txt

## Launch NEXUS

    ./nexus

## Original Web Application

    bash scripts/ops.sh start

Web address: http://127.0.0.1:8095/

## Testing

    .venv-nexus/bin/python -m pytest tests/nexus -q

## Continuous Integration

The repository includes the original Linux verification workflow
and a separate NEXUS Python 3.14 testing workflow.

GitHub-hosted CI execution has not yet been verified.

## Security

NEXUS is intended for local educational use.
Do not expose its development HTTP server to the internet.

## Project Background

Built upon the DecodeLabs Linux Operations Lab while
preserving the original Bash toolkit and web application.
