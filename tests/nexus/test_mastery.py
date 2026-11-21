from nexus_ui.services.mastery import CommandLab


def test_navigation(tmp_path):
    lab = CommandLab(tmp_path / "lab")

    assert lab.run("pwd").success
    assert lab.run("mkdir -p app/logs").success
    assert lab.run("cd app").success
    assert lab.cwd.name == "app"
    assert lab.run("cd ..").success
    assert lab.cwd == lab.root
    assert lab.run("cd -").success
    assert lab.cwd.name == "app"
    assert lab.run("cd ~").success


def test_file_operations(tmp_path):
    lab = CommandLab(tmp_path / "lab")

    assert lab.run("touch config.conf").success
    assert lab.run("echo Started > server.log").success
    assert lab.run("cat server.log").output == "Started\n"
    assert lab.run("cp server.log copy.log").success
    assert lab.run("mv copy.log server.bak").success
    assert lab.run("rm server.bak").success

    assert not (lab.root / "server.bak").exists()


def test_permissions(tmp_path):
    lab = CommandLab(tmp_path / "lab")

    assert lab.run("touch config.conf").success
    assert lab.run("chmod 600 config.conf").success

    assert (
        (lab.root / "config.conf").stat().st_mode
        & 0o777
    ) == 0o600


def test_path_boundary(tmp_path):
    lab = CommandLab(tmp_path / "lab")

    assert not lab.run("cd /etc").success
    assert not lab.run("cat /etc/passwd").success
    assert not lab.run("touch ../outside").success
    assert not lab.run("rm -rf /").success
    assert not lab.run("sudo whoami").success
    assert not lab.run("bash").success

    assert not (tmp_path / "outside").exists()


def test_symlink_boundary(tmp_path):
    lab = CommandLab(tmp_path / "lab")

    outside = tmp_path / "outside.txt"
    outside.write_text("Protected")

    (lab.root / "link").symlink_to(outside)

    assert not lab.run("cat link").success
    assert not lab.run("echo Changed > link").success

    assert outside.read_text() == "Protected"


def test_identity_and_help(tmp_path):
    lab = CommandLab(tmp_path / "lab")

    assert lab.run("whoami").success
    assert lab.run("id").success
    assert lab.run("help").success
    assert "mkdir" in lab.run("help").output


def test_history(tmp_path):
    lab = CommandLab(tmp_path / "lab")

    lab.run("pwd")
    lab.run("invalid-command")

    assert len(lab.history) == 2
    assert lab.history[0].success
    assert not lab.history[1].success
