# Linux Engineering Command Reference

| Command | Purpose | Practical usage |
|---|---|---|
| pwd | Current directory | pwd |
| ls | List contents | ls -la |
| cd | Change directory | cd app |
| mkdir | Create directories | mkdir -p app/logs |
| touch | Create empty files | touch example.txt |
| cp | Copy data | cp source.txt backup.txt |
| mv | Move or rename | mv server.log server.bak |
| rm | Remove files | rm -i example.txt |
| cat | Display file contents | cat app/config.conf |
| less | Interactive inspection | less app/logs/server.log |
| head | Read first lines | head -n 5 server.log |
| tail | Read final lines | tail -n 10 server.log |
| tail -f | Follow log changes | tail -f server.log |
| grep | Search text | grep 404 server.log |
| whoami | Current username | whoami |
| id | User and group identity | id |
| groups | Group memberships | groups |
| chmod | File permissions | chmod 750 script.sh |
| chown | File ownership | chown user:group file |
| stat | File metadata | stat file |
| umask | Default permissions | umask 077 |
| find | Locate filesystem objects | find app -type f |
| ps | Inspect processes | ps aux |
| ss | Inspect network sockets | ss -ltnp |
| curl | HTTP requests | curl http://localhost:8095 |
| tar | Archive files | tar -czf backup.tar.gz app |
| sha256sum | Integrity verification | sha256sum backup.tar.gz |
| cmp | Byte-level file comparison | cmp file1 file2 |
| diff | Compare files | diff -r source backup |
| tee | Save and display output | command \| tee report.txt |
| du | Disk usage | du -h app |
| ssh | Secure remote access | ssh user@host |
| bash -n | Validate shell syntax | bash -n script.sh |

## Permission Model

Read = 4, Write = 2, Execute = 1.

- 600: Owner read/write.
- 640: Owner read/write, group read.
- 644: Owner read/write, group and others read.
- 700: Owner full access.
- 750: Owner full access, group read/execute.
- 755: Owner full access, group and others read/execute.

## Safety Practices

Verify the working directory with pwd before
performing destructive operations.

Use rm -i when practicing file deletion.

Avoid unnecessary sudo privileges.

Never commit credentials, private configuration
or sensitive operational logs.
