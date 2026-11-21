import pytest

from nexus_ui.services.reports import checksum

from nexus_ui.services.report_archive import (
    verify_report,
    list_reports,
)


def create_report(tmp_path):

    folder = tmp_path / "engineering-test"
    folder.mkdir()

    for name in ("report.md", "report.json"):
        (folder / name).write_text("test evidence")

    (folder / "SHA256SUMS").write_text(
        "".join(
            f"{checksum(folder / name)}  {name}\n"
            for name in ("report.md", "report.json")
        )
    )

    return folder


def test_valid_report(tmp_path):

    folder = create_report(tmp_path)

    result = verify_report(folder, tmp_path)

    assert result["passed"]
    assert len(result["checks"]) == 2


def test_modified_report(tmp_path):

    folder = create_report(tmp_path)

    (folder / "report.md").write_text("modified")

    result = verify_report(folder, tmp_path)

    assert not result["passed"]
    assert not result["checks"]["report.md"]


def test_invalid_manifest(tmp_path):

    folder = create_report(tmp_path)

    (folder / "SHA256SUMS").write_text(
        "a" * 64 + "  ../outside\n"
    )

    with pytest.raises(ValueError):
        verify_report(folder, tmp_path)


def test_symlink_rejected(tmp_path):

    folder = create_report(tmp_path)

    outside = tmp_path / "outside"

    outside.write_text("test")

    (folder / "report.md").unlink()

    (folder / "report.md").symlink_to(outside)

    with pytest.raises(ValueError):
        verify_report(folder, tmp_path)


def test_archive_inventory(tmp_path):

    folder = create_report(tmp_path)

    assert list_reports(tmp_path) == [folder]
