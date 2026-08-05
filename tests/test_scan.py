"""Tests for `viparse scan` — the survey that converts nothing.

The command exists to answer the question that comes before conversion: *do I even have
this problem?* Its whole value is that the number it reports is the reader's own, so the
tests here are about it being **right** and about it never quietly covering less than it
claims.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from viparse.cli import main
from viparse.detect import SUPPORTED_SUFFIXES
from viparse.scan import format_report, scan

docx = pytest.importorskip("docx")


def _docx(path: Path, text: str, font: str | None = None) -> Path:
    document = docx.Document()
    run = document.add_paragraph().add_run(text)
    if font:
        run.font.name = font
    document.save(str(path))
    return path


def test_scan_separates_legacy_from_unicode(tmp_path: Path) -> None:
    _docx(tmp_path / "cu.docx", "B¸o c¸o tµi chÝnh", ".VnTime")
    _docx(tmp_path / "moi.docx", "Báo cáo tài chính")

    report = scan(sorted(tmp_path.glob("*.docx")))
    assert [f.encoding for f in report.legacy] == ["tcvn3"]
    assert len(report.clean) == 1


def test_scan_converts_nothing_and_writes_nothing(tmp_path: Path) -> None:
    """The one property a survey must have: it does not touch the files it surveys."""
    source = _docx(tmp_path / "cu.docx", "B¸o c¸o", ".VnTime")
    before = source.read_bytes()
    listing = sorted(p.name for p in tmp_path.iterdir())

    scan([source])

    assert source.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == listing


def test_unreadable_files_are_not_counted_as_clean(tmp_path: Path) -> None:
    """Counting a file viparse could not read as "already Unicode" is the one dishonest
    outcome available here — it would understate the problem it exists to reveal."""
    broken = tmp_path / "hong.docx"
    broken.write_bytes(b"PK\x03\x04 not really a docx")

    report = scan([broken])
    assert len(report.unreadable) == 1
    assert not report.clean


def test_directory_expansion_covers_every_supported_format(tmp_path: Path) -> None:
    """The regression this command was built on top of.

    Directory expansion filtered on `("*.docx",)`, so `viparse ./docs` silently skipped
    every .doc, .pdf, .xls, .rtf and .ppt in the tree and reported success. A scan that
    covers a fraction of a directory is worse than no scan.
    """
    from viparse.cli import _expand

    for suffix in SUPPORTED_SUFFIXES:
        (tmp_path / f"file{suffix}").write_bytes(b"x")
    found = {p.suffix.lower() for p in _expand(str(tmp_path))}
    assert found == set(SUPPORTED_SUFFIXES)


def test_directory_expansion_is_case_insensitive(tmp_path: Path) -> None:
    # Scanners and archives write .PDF and .TIF; a filter that misses them covers less
    # than it says it does.
    from viparse.cli import _expand

    (tmp_path / "scan.PDF").write_bytes(b"%PDF-1.4\n")
    (tmp_path / "archive.TIF").write_bytes(b"II*\x00")
    assert len(_expand(str(tmp_path))) == 2


def test_directory_expansion_ignores_unsupported_files(tmp_path: Path) -> None:
    from viparse.cli import _expand

    (tmp_path / "notes.txt").write_text("not a document")
    (tmp_path / "a.docx").write_bytes(b"PK\x03\x04")
    assert [p.name for p in _expand(str(tmp_path))] == ["a.docx"]


def test_report_names_the_encodings_found(tmp_path: Path) -> None:
    _docx(tmp_path / "a.docx", "B¸o c¸o tµi chÝnh", ".VnTime")
    text = format_report(scan(sorted(tmp_path.glob("*.docx"))))
    assert "tcvn3 1" in text
    assert "mojibake" in text


def test_report_says_so_when_there_is_nothing_to_do(tmp_path: Path) -> None:
    _docx(tmp_path / "a.docx", "Báo cáo tài chính")
    assert "Nothing here needs viparse" in format_report(scan(sorted(tmp_path.glob("*.docx"))))


def test_report_never_truncates_the_file_list_silently(tmp_path: Path) -> None:
    for i in range(5):
        _docx(tmp_path / f"f{i}.docx", "B¸o c¸o", ".VnTime")
    text = format_report(scan(sorted(tmp_path.glob("*.docx"))), show_files=2)
    assert "and 3 more" in text


def test_cli_scan_exits_1_when_legacy_files_are_found(tmp_path: Path, capsys) -> None:  # noqa: ANN001
    _docx(tmp_path / "cu.docx", "B¸o c¸o tµi chÝnh", ".VnTime")
    assert main(["scan", str(tmp_path)]) == 1
    assert "legacy encoding" in capsys.readouterr().out


def test_cli_scan_exits_0_when_nothing_is_found(tmp_path: Path) -> None:
    _docx(tmp_path / "moi.docx", "Báo cáo tài chính")
    assert main(["scan", str(tmp_path)]) == 0
