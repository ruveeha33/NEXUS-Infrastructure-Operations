from pathlib import Path
import os
import stat
import pwd
import grp
import socket
import subprocess

import psutil

ROOT = Path(__file__).resolve().parents[2]


def processes():
    rows = []

    for proc in psutil.process_iter(
        ["pid", "name", "username",
         "memory_info", "status", "cpu_times"]
    ):
        try:
            info = proc.info
            memory = info.get("memory_info")
            cpu = info.get("cpu_times")

            rows.append((
                str(info["pid"]),
                str(info.get("name") or "-"),
                str(info.get("username") or "-"),
                f"{memory.rss / 1024**2:.1f}"
                if memory else "-",
                f"{cpu.user + cpu.system:.1f}"
                if cpu else "-",
                str(info.get("status") or "-"),
            ))
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue

    return sorted(rows, key=lambda r: int(r[0]))


def filesystem(relative="."):
    target = (ROOT / relative).resolve()

    if not target.is_relative_to(ROOT):
        raise PermissionError(
            "Navigation outside project is restricted."
        )

    if not target.is_dir():
        raise NotADirectoryError(target)

    rows = []

    for entry in sorted(
        target.iterdir(),
        key=lambda p: (not p.is_dir(), p.name.lower())
    ):
        try:
            info = entry.lstat()

            try:
                owner = pwd.getpwuid(
                    info.st_uid
                ).pw_name
            except KeyError:
                owner = str(info.st_uid)

            try:
                group = grp.getgrgid(
                    info.st_gid
                ).gr_name
            except KeyError:
                group = str(info.st_gid)

            kind = (
                "LINK" if entry.is_symlink()
                else "DIR" if entry.is_dir()
                else "FILE"
            )

            rows.append((
                entry.name,
                kind,
                stat.filemode(info.st_mode),
                owner,
                group,
                f"{info.st_size:,}",
            ))
        except OSError:
            continue

    return rows


def interfaces():
    rows = []
    status = psutil.net_if_stats()

    for name, addresses in (
        psutil.net_if_addrs().items()
    ):
        for address in addresses:
            if address.family not in (
                socket.AF_INET,
                socket.AF_INET6,
            ):
                continue

            state = status.get(name)

            rows.append((
                name,
                "UP" if state and state.isup else "DOWN",
                "IPv4"
                if address.family == socket.AF_INET
                else "IPv6",
                address.address,
                address.netmask or "-",
            ))

    return rows


def endpoint(address):
    if not address:
        return "-"

    host = address.ip
    if ":" in host:
        host = f"[{host}]"

    return f"{host}:{address.port}"


def connections():
    rows = []

    for conn in psutil.net_connections(kind="inet"):
        protocol = (
            "TCP"
            if conn.type == socket.SOCK_STREAM
            else "UDP"
        )

        rows.append((
            protocol,
            endpoint(conn.laddr),
            endpoint(conn.raddr),
            str(conn.status),
            str(conn.pid or "-"),
        ))

    return sorted(rows, key=lambda r: (
        r[3] != "LISTEN", r[1]
    ))


def git_command(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
            or "Git operation failed"
        )

    return result.stdout.strip()


def repository():
    branch = git_command(
        "branch", "--show-current"
    )
    commit = git_command(
        "rev-parse", "--short", "HEAD"
    )
    status = git_command(
        "status", "--short"
    )

    return [
        ("Branch", branch),
        ("Commit", commit),
        ("Working tree",
         "Modified" if status else "Clean"),
        ("Repository",
         git_command("rev-parse", "--show-toplevel")),
        ("Tracked files",
         str(len(
             git_command("ls-files").splitlines()
         ))),
        ("Recent commits",
         git_command("log", "-1", "--format=%s")),
    ]


def commits():
    raw = git_command(
        "log", "-15",
        "--format=%h%x09%ad%x09%s",
        "--date=short",
    )

    return [
        tuple(line.split("\t", 2))
        for line in raw.splitlines()
        if line
    ]
