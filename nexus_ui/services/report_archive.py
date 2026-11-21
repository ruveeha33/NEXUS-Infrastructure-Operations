"""Local engineering report inventory and verification."""

import json
import stat

from pathlib import Path

from nexus_ui.services.reports import (
    REPORTS,
    checksum,
)


def list_reports(directory=REPORTS):

    directory = Path(directory)

    if not directory.is_dir():
        return []

    reports = []

    for folder in directory.glob("engineering-*"):

        if folder.is_symlink() or not folder.is_dir():
            continue

        if not folder.resolve().is_relative_to(
            directory.resolve()
        ):
            continue

        reports.append(folder)

    return sorted(
        reports,
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def verify_report(folder, directory=REPORTS):

    folder = Path(folder)
    directory = Path(directory).resolve()

    if folder.is_symlink():
        raise ValueError("Symlink report rejected")

    folder = folder.resolve()

    if folder.parent != directory:
        raise ValueError("Report outside archive")

    if not folder.name.startswith("engineering-"):
        raise ValueError("Invalid report directory")

    expected = {"report.md", "report.json"}

    manifest = folder / "SHA256SUMS"

    for path in [
        manifest,
        folder / "report.json",
        folder / "report.md",
    ]:

        if path.is_symlink():
            raise ValueError("Symlink artifact rejected")

        if not stat.S_ISREG(path.stat().st_mode):
            raise ValueError("Invalid report artifact")

        if path.stat().st_size > 10_000_000:
            raise ValueError("Oversized report artifact")

    checks = {}

    for line in manifest.read_text().splitlines():

        digest, filename = line.split("  ", 1)

        if filename not in expected:
            raise ValueError("Unexpected manifest entry")

        if filename in checks:
            raise ValueError("Duplicate manifest entry")

        if (
            len(digest) != 64
            or any(
                char not in "0123456789abcdef"
                for char in digest
            )
        ):
            raise ValueError("Invalid SHA-256 digest")

        checks[filename] = (
            checksum(folder / filename) == digest
        )

    if set(checks) != expected:
        raise ValueError("Incomplete integrity manifest")

    return {
        "passed": all(checks.values()),
        "checks": checks,
    }


def load_latest(directory=REPORTS):

    folders = list_reports(directory)

    if not folders:
        return None

    folder = folders[0]

    integrity = verify_report(
        folder,
        directory,
    )

    if not integrity["passed"]:
        raise ValueError("Report integrity check failed")

    data = json.loads(
        (folder / "report.json").read_text()
    )

    return {
        "directory": str(folder),
        "data": data,
        "integrity": integrity,
    }
