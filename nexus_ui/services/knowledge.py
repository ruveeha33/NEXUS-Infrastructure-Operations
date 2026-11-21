"""Linux filesystem intelligence and learning content."""

import os
import stat
import pwd
import grp

from pathlib import Path
from itertools import islice


DIRECTORIES = {
    "/": (
        "Root filesystem",
        "The starting point of the Linux filesystem tree.",
    ),
    "/bin": (
        "Essential user commands",
        "Core command binaries such as ls and cat. "
        "Modern distributions may link this to /usr/bin.",
    ),
    "/boot": (
        "Boot resources",
        "Kernel and bootloader resources. "
        "WSL may not use conventional boot files.",
    ),
    "/dev": (
        "Device interfaces",
        "Special files exposing device interfaces.",
    ),
    "/etc": (
        "System configuration",
        "Host-wide operating system and service settings.",
    ),
    "/home": (
        "User home directories",
        "Personal files and settings for regular users.",
    ),
    "/root": (
        "Administrator home",
        "Private home directory of the root account.",
    ),
    "/sbin": (
        "System administration binaries",
        "Administrative tools, often linked to /usr/sbin.",
    ),
    "/tmp": (
        "Temporary storage",
        "Temporary files. Commonly protected by a sticky bit.",
    ),
    "/usr": (
        "Installed software resources",
        "Applications, libraries, binaries and shared resources.",
    ),
    "/var": (
        "Variable application data",
        "Logs, caches, databases and changing service data.",
    ),
    "/proc": (
        "Process information",
        "Virtual filesystem exposing kernel and process information.",
    ),
    "/sys": (
        "Kernel device information",
        "Virtual filesystem representing kernel objects.",
    ),
    "/opt": (
        "Optional software",
        "Additional application packages.",
    ),
    "/run": (
        "Runtime state",
        "Transient service state and runtime information.",
    ),
    "/mnt": (
        "Mount points",
        "Mounted filesystems, including Windows drives in WSL.",
    ),
}


LESSONS = [
    (
        "01 / Navigation",
        """NAVIGATION AND CONTEXT

pwd
    Print the current working directory.

cd directory
    Enter a directory.

cd ..
    Move to the parent directory.

cd ~
    Return to the home directory.

cd -
    Return to the previous directory.

ls -l
    Display detailed file metadata.

ls -a
    Include hidden files.

ls -R
    List directories recursively.

ENGINEERING PRINCIPLE
Always verify your location before modifying files.

PRACTICE
pwd
mkdir -p app/logs
cd app
ls -la
cd ..
""",
    ),
    (
        "02 / Filesystem hierarchy",
        """FILESYSTEM HIERARCHY

/       Root filesystem
/bin    Essential commands
/boot   Boot resources
/dev    Device interfaces
/etc    System configuration
/home   Regular user directories
/root   Administrator home
/sbin   Administration commands
/tmp    Temporary files
/usr    Installed software resources
/var    Variable data and logs

ENGINEERING PRINCIPLE
Store configuration, logs and application files
according to their intended purpose.

Use the FHS Explorer to inspect actual metadata.
""",
    ),
    (
        "03 / File operations",
        """FILE ENGINEERING

mkdir -p app/logs
    Create nested directories.

touch app/config.conf
    Create an empty file.

cp source destination
    Copy a file.

mv old new
    Rename or move a file.

rm filename
    Remove a file.

rmdir directory
    Remove an empty directory.

PRACTICE
touch example.txt
cp example.txt copy.txt
mv copy.txt backup.txt
rm backup.txt

Deletion is not automatically reversible.
""",
    ),
    (
        "04 / Log inspection",
        """LOG ENGINEERING

cat filename
    Display file contents.

less filename
    Inspect a file interactively.

head filename
    Display the first ten lines.

tail filename
    Display the last ten lines.

tail -f filename
    Follow newly appended log entries.

PRACTICE IN COMMAND LAB
echo Started > server.log
cat server.log
head server.log
tail server.log

Use NEXUS Event Stream for operational logs.
less and tail -f belong in a normal terminal.
""",
    ),
    (
        "05 / Permissions",
        """LINUX ACCESS CONTROL

-rwxr-xr--

-    Regular file
rwx  Owner permissions
r-x  Group permissions
r--  Other permissions

NUMERIC VALUES

Read       = 4
Write      = 2
Execute    = 1

754 = rwx r-x r--
600 = rw- --- ---
755 = rwx r-x r-x

PRACTICE
touch example.sh
chmod 754 example.sh
ls -l example.sh

ENGINEERING PRINCIPLE
Grant only the permissions actually required.
""",
    ),
    (
        "06 / User identity",
        """IDENTITY AND OWNERSHIP

whoami
    Display current effective username.

id
    Display user ID and group memberships.

ls -l filename
    Display file owner and group.

chown USER:GROUP filename
    Change file ownership when authorized.

PRACTICE
whoami
id
touch identity.txt
ls -l identity.txt

Ownership changes are not enabled inside
the restricted Command Lab.
""",
    ),
    (
        "07 / Secure Shell",
        """SECURE SHELL (SSH)

ssh user@host

SSH provides encrypted remote access to
another computer running an SSH server.

CLIENT
Initiates the connection.

SERVER
Authenticates the connecting user.

HOST KEY
Helps verify server identity.

PUBLIC KEY AUTHENTICATION
Uses a cryptographic key pair.

SECURITY PRINCIPLES
Verify host keys.
Protect private keys.
Use authorized accounts and systems.

This module explains SSH.
A live SSH exercise is a later phase.
""",
    ),
    (
        "08 / Safe operations",
        """SAFE LINUX ENGINEERING

pwd
    Confirm your current directory.

ls -l
    Inspect ownership and permissions.

rm -i filename
    Request confirmation before deletion.

rm -rf directory
    Recursive forced deletion. High consequence.

Never run destructive commands without
verifying the exact target and authorization.

Operational sequence:

1. Inspect.
2. Verify context.
3. Back up important data.
4. Execute the intended operation.
5. Validate the result.

The restricted Command Lab deliberately
blocks recursive forced deletion.
""",
    ),
    (
        "09 / Intern mission",
        """DECODELABS PRACTICAL MISSION

Complete the following inside Linux Lab.
The relative app directory represents
the assignment's /app practice location.

mkdir -p app/logs

touch app/config.conf

echo Started > app/logs/server.log

pwd

ls -R app

mv app/logs/server.log app/logs/server.bak

ls -l app/config.conf

Open Linux Lab using M.
The mission tracker checks six objectives.
""",
    ),
]


def inspect_directory(location):

    if location not in DIRECTORIES:
        raise ValueError("Directory is not in curated FHS list")

    path = Path(location)

    title, description = DIRECTORIES[location]

    result = {
        "path": location,
        "title": title,
        "description": description,
        "available": False,
        "entries": [],
    }

    try:
        info = path.stat()

        try:
            owner = pwd.getpwuid(info.st_uid).pw_name
        except KeyError:
            owner = str(info.st_uid)

        try:
            group = grp.getgrgid(info.st_gid).gr_name
        except KeyError:
            group = str(info.st_gid)

        result.update({
            "available": True,
            "resolved": str(path.resolve()),
            "owner": owner,
            "group": group,
            "permissions": stat.filemode(info.st_mode),
            "octal": oct(stat.S_IMODE(info.st_mode)),
            "readable": os.access(path, os.R_OK),
            "writable": os.access(path, os.W_OK),
        })

        try:
            with os.scandir(path) as entries:
                result["entries"] = sorted(
                    entry.name
                    for entry in islice(entries, 40)
                )

        except OSError as exc:
            result["listing_error"] = str(exc)

    except OSError as exc:
        result["error"] = str(exc)

    return result
