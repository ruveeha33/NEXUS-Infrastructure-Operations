# Technical Architecture

## Design Objective

Create a reproducible Linux operations environment
for demonstrating foundational DevOps engineering.

## Application Layer

The static HTML application is stored in app/index.html.
The setup script copies it into app/public/index.html.

Python's HTTP server exposes only app/public.

## Configuration Layer

The local configuration defines the application name,
version, environment, network host, port and log level.

The configuration is trusted local Bash configuration.
It must not contain untrusted shell instructions.

## Operations Layer

The operations CLI delegates commands to dedicated
Bash scripts for deployment, monitoring, security,
backup, recovery and verification.

## Observability Layer

Server activity is recorded in app/logs/server.log.

The monitoring script summarizes HTTP requests,
status codes, service availability and log size.

HTTP 304 indicates a cached resource is still valid.
HTTP 404 indicates a missing requested resource.

## Security Boundaries

The server binds to 127.0.0.1.
Sensitive files remain outside the public directory.

Linux permissions restrict access to configuration,
logs, scripts and backup archives.

## Recovery Layer

Timestamped tar.gz archives preserve application
assets and operational scripts.

SHA-256 checksums detect archive changes when
compared against the trusted recorded checksum.

Recovery testing takes place in isolated directories.

Runtime logs are not included in application backups.

## Verification Layer

The acceptance suite checks filesystem structure,
configuration, HTTP behavior, local network binding,
script functionality, permissions and file recovery.

## Continuous Integration

GitHub Actions reproduces the initialization,
deployment and validation workflow on a Linux runner.

## Operational Scope

This is a single-host, local development lab.
It is not a production deployment architecture.
