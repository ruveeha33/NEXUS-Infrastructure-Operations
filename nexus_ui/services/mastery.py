"""Restricted Linux command laboratory."""

import os
import shlex
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "evidence" / "linux-lab"

COMMANDS = {
    "ls": {"-l", "-a", "-la", "-al", "-R", "-h", "-lh"},
    "mkdir": {"-p"},
    "touch": set(),
    "cat": set(),
    "head": set(),
    "tail": set(),
    "cp": set(),
    "mv": set(),
    "rm": set(),
    "rmdir": set(),
    "stat": set(),
    "chmod": set(),
    "whoami": set(),
    "id": set(),
}

HELP = {
    "pwd": "Print the current working directory.",
    "cd": "Change working directory.",
    "ls": "List files and directories.",
    "mkdir": "Create directories.",
    "touch": "Create an empty file or update timestamps.",
    "cat": "Display file contents.",
    "head": "Display the first ten lines.",
    "tail": "Display the last ten lines.",
    "cp": "Copy a file.",
    "mv": "Move or rename a file.",
    "rm": "Remove a file.",
    "rmdir": "Remove an empty directory.",
    "stat": "Display filesystem metadata.",
    "chmod": "Change file permissions.",
    "whoami": "Display the current username.",
    "id": "Display user and group identities.",
    "echo": "Display text or write it to a lab file.",
}


@dataclass
class Result:
    success: bool
    output: str
    command: str


class CommandLab:

    def __init__(self, root=LAB):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.root.chmod(0o700)
        self.cwd = self.root
        self.previous = self.root
        self.history = []

    def path(self, value):
        candidate = (
            self.root if value == "~"
            else self.cwd / value
        )

        resolved = candidate.resolve()

        if not resolved.is_relative_to(self.root):
            raise ValueError("Path leaves the practice workspace")

        return resolved

    def run(self, command):
        try:
            result = self.execute(command)
        except Exception as exc:
            result = Result(False, str(exc), command)

        self.history.append(result)
        return result

    def execute(self, command):
        if len(command) > 4096:
            raise ValueError("Command too long")

        parts = shlex.split(command)

        if not parts:
            return Result(True, "", command)

        name, *args = parts

        if name == "help":
            output = "\n".join(
                f"{key:10} {description}"
                for key, description in HELP.items()
            )
            return Result(True, output, command)

        if name == "pwd":
            if args:
                raise ValueError("Usage: pwd")
            return Result(True, str(self.cwd), command)

        if name == "cd":
            if len(args) > 1:
                raise ValueError("Usage: cd [directory]")

            target = args[0] if args else "~"

            destination = (
                self.previous if target == "-"
                else self.path(target)
            )

            if not destination.is_dir():
                raise ValueError("Directory does not exist")

            self.previous, self.cwd = self.cwd, destination

            return Result(True, str(self.cwd), command)

        if name == "echo":
            if ">" in args:
                index = args.index(">")

                if len(args) != index + 2:
                    raise ValueError(
                        "Usage: echo TEXT > FILE"
                    )

                target = self.path(args[-1])
                target.write_text(
                    " ".join(args[:index]) + "\n"
                )

                return Result(
                    True,
                    f"Written: {target.name}",
                    command,
                )

            return Result(
                True,
                " ".join(args),
                command,
            )

        if name not in COMMANDS:
            raise ValueError(
                "Command unavailable in restricted lab. "
                "Type help."
            )

        flags = []
        operands = []

        for arg in args:
            if arg.startswith("-"):
                if arg not in COMMANDS[name]:
                    raise ValueError(
                        f"Unsupported option: {arg}"
                    )

                flags.append(arg)
            else:
                operands.append(arg)

        prefix = []

        if name == "chmod":
            if len(operands) != 2:
                raise ValueError(
                    "Usage: chmod MODE FILE"
                )

            mode = operands.pop(0)

            if len(mode) != 3 or any(
                c not in "01234567" for c in mode
            ):
                raise ValueError(
                    "Use a three-digit octal mode"
                )

            prefix.append(mode)

        if name in {"whoami", "id"} and operands:
            raise ValueError("Arguments not supported")

        if name == "ls" and not operands:
            operands = ["."]

        if name in {"cp", "mv"} and len(operands) != 2:
            raise ValueError(
                f"Usage: {name} SOURCE DESTINATION"
            )

        paths = [str(self.path(p)) for p in operands]

        if name in {"rm", "rmdir", "mv", "chmod"}:
            if str(self.root) in paths:
                raise ValueError(
                    "Practice root is protected"
                )

        executable = shutil.which(
            name, path="/usr/bin:/bin"
        )

        if not executable:
            raise ValueError("Linux command unavailable")

        environment = {
            "PATH": "/usr/bin:/bin",
            "HOME": str(self.root),
            "LANG": "C.UTF-8",
        }

        completed = subprocess.run(
            [executable, *flags, *prefix, *paths],
            cwd=self.cwd,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=5,
            shell=False,
        )

        output = completed.stdout[:20000]

        return Result(
            completed.returncode == 0,
            output or (
                "Completed successfully"
                if completed.returncode == 0
                else "Command failed"
            ),
            command,
        )
