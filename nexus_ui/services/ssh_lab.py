"""Temporary localhost OpenSSH training mission."""

import os
import time
import getpass
import socket
import tempfile
import subprocess

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOST = "127.0.0.1"
PORT = 22222


def run(args, timeout=10):
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def checked(args):
    result = run(args)

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr or result.stdout
        )

    return result.stdout.strip()


def port_open():
    with socket.socket() as connection:
        connection.settimeout(0.5)

        return connection.connect_ex(
            (HOST, PORT)
        ) == 0


def ssh_mission(emit=print):

    if os.getuid() == 0:
        raise RuntimeError("Do not run NEXUS as root")

    if port_open():
        raise RuntimeError("SSH training port occupied")

    user = getpass.getuser()

    with tempfile.TemporaryDirectory(
        prefix="ssh-session-",
        dir=ROOT / "evidence",
    ) as directory:

        lab = Path(directory)
        server = None

        try:
            for key in (
                "client_key",
                "host_key",
                "rejected_key",
            ):
                checked([
                    "ssh-keygen",
                    "-q",
                    "-t", "ed25519",
                    "-N", "",
                    "-f", str(lab / key),
                ])

                (lab / key).chmod(0o600)

            emit("[PASS] Ephemeral ED25519 keys generated")

            handler = lab / "remote-command.sh"

            handler.write_text(
                """#!/bin/sh
case "${SSH_ORIGINAL_COMMAND:-}" in
    health) printf '%s\\n' NEXUS_SSH_OK ;;
    whoami) exec /usr/bin/whoami ;;
    hostname) exec /usr/bin/hostname ;;
    id) exec /usr/bin/id ;;
    pwd) exec /usr/bin/pwd ;;
    "uname -s") exec /usr/bin/uname -s ;;
    *)
        echo "Command rejected by NEXUS policy"
        exit 126
        ;;
esac
"""
            )

            handler.chmod(0o700)

            public_key = (
                lab / "client_key.pub"
            ).read_text().strip()

            authorization = lab / "authorized_keys"

            authorization.write_text(
                f'restrict,command="{handler}" '
                f'{public_key}\n'
            )

            authorization.chmod(0o600)

            host_key = (
                lab / "host_key.pub"
            ).read_text().split()

            known_hosts = lab / "known_hosts"

            known_hosts.write_text(
                f"[{HOST}]:{PORT} "
                f"{host_key[0]} {host_key[1]}\n"
            )

            known_hosts.chmod(0o600)

            config = lab / "sshd_config"

            config.write_text(f"""
Port {PORT}
ListenAddress {HOST}
HostKey {lab / 'host_key'}
PidFile {lab / 'sshd.pid'}
AuthorizedKeysFile {authorization}
AllowUsers {user}
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
AuthenticationMethods publickey
PermitRootLogin no
PermitEmptyPasswords no
UsePAM no
DisableForwarding yes
PermitTunnel no
PermitTTY no
PermitUserEnvironment no
PermitUserRC no
StrictModes yes
LogLevel VERBOSE
""")

            checked([
                "/usr/sbin/sshd",
                "-t", "-f", str(config),
            ])

            emit("[PASS] SSH configuration verified")

            logfile = lab / "server.log"

            with logfile.open("w") as output:
                server = subprocess.Popen(
                    [
                        "/usr/sbin/sshd",
                        "-D", "-e",
                        "-f", str(config),
                    ],
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    close_fds=True,
                )

            for _ in range(30):

                if server.poll() is not None:
                    raise RuntimeError(
                        logfile.read_text()
                    )

                if port_open():
                    break

                time.sleep(0.1)

            else:
                raise RuntimeError(
                    "SSH startup timed out"
                )

            emit(f"[PASS] SSH listening on {HOST}:{PORT}")

            def remote(command, key="client_key",
                       hosts=known_hosts):

                return run([
                    "ssh",
                    "-F", "/dev/null",
                    "-p", str(PORT),
                    "-i", str(lab / key),
                    "-o", "IdentitiesOnly=yes",
                    "-o", "IdentityAgent=none",
                    "-o", "BatchMode=yes",
                    "-o", "StrictHostKeyChecking=yes",
                    "-o", f"UserKnownHostsFile={hosts}",
                    "-o", "GlobalKnownHostsFile=/dev/null",
                    "-o", "ConnectTimeout=5",
                    f"{user}@{HOST}",
                    command,
                ])

            for command in (
                "health",
                "whoami",
                "hostname",
                "id",
                "pwd",
                "uname -s",
            ):

                result = remote(command)

                if result.returncode != 0:
                    raise RuntimeError(result.stderr)

                output = result.stdout.strip()

                if command == "health":
                    assert output == "NEXUS_SSH_OK"

                if command == "whoami":
                    assert output == user

                if command == "uname -s":
                    assert output == "Linux"

                emit(f"\nremote$ {command}")
                emit(output)

            emit("\n[PASS] Encrypted SSH execution verified")

            rejected = remote("cat /etc/passwd")

            assert rejected.returncode == 126
            assert "rejected" in rejected.stdout

            emit("[PASS] Unauthorized command rejected")

            rejected = remote(
                "health",
                key="rejected_key",
            )

            assert rejected.returncode == 255
            assert "Permission denied" in rejected.stderr

            emit("[PASS] Unauthorized key rejected")

            bad_hosts = lab / "bad_known_hosts"

            wrong = (
                lab / "rejected_key.pub"
            ).read_text().split()

            bad_hosts.write_text(
                f"[{HOST}]:{PORT} "
                f"{wrong[0]} {wrong[1]}\n"
            )

            rejected = remote(
                "health",
                hosts=bad_hosts,
            )

            assert rejected.returncode == 255
            assert (
                "Host key verification failed"
                in rejected.stderr
            )

            emit("[PASS] Incorrect host key rejected")

            logs = logfile.read_text()

            assert "Accepted publickey" in logs
            assert "Failed publickey" in logs

            emit("[PASS] Authentication evidence verified")

            emit(
                checked([
                    "ssh-keygen",
                    "-lf",
                    str(lab / "host_key.pub"),
                ])
            )

        finally:

            if server is not None and server.poll() is None:
                server.terminate()

                try:
                    server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=5)

    if port_open():
        raise RuntimeError("Training port not released")

    emit("[PASS] Temporary SSH server stopped")
    emit("[PASS] Session keys and temporary files removed")
    emit("[PASS] SSH mission complete")

    return True
