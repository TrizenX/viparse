"""Golden tests for magic-byte format detection."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from viparse.detect import (
    _OLE2_MAGIC,
    CONTENT_TYPE_DOCX,
    CONTENT_TYPE_JPEG,
    CONTENT_TYPE_OLE2,
    CONTENT_TYPE_PDF,
    CONTENT_TYPE_PNG,
    CONTENT_TYPE_PPTX,
    CONTENT_TYPE_RTF,
    CONTENT_TYPE_TIFF,
    CONTENT_TYPE_XLSX,
    detect_format,
)
from viparse.errors import UnsupportedFormat


def _write(path: Path, data: bytes) -> Path:
    path.write_bytes(data)
    return path


def _write_zip(path: Path, entries: list[str]) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        for name in entries:
            zf.writestr(name, "x")
    return path


def test_detects_docx(tmp_path: Path) -> None:
    f = _write_zip(tmp_path / "a.docx", ["[Content_Types].xml", "word/document.xml"])
    assert detect_format(f).content_type == CONTENT_TYPE_DOCX


def test_detects_xlsx(tmp_path: Path) -> None:
    f = _write_zip(tmp_path / "a.xlsx", ["xl/workbook.xml"])
    assert detect_format(f).content_type == CONTENT_TYPE_XLSX


def test_detects_pptx(tmp_path: Path) -> None:
    f = _write_zip(tmp_path / "a.pptx", ["ppt/presentation.xml"])
    assert detect_format(f).content_type == CONTENT_TYPE_PPTX


def test_detects_rtf(tmp_path: Path) -> None:
    f = _write(tmp_path / "a.rtf", rb"{\rtf1\ansi hello\par}")
    assert detect_format(f).content_type == CONTENT_TYPE_RTF


def test_detects_rtf_with_utf8_bom(tmp_path: Path) -> None:
    """An editor's leading UTF-8 BOM before {\\rtf must not defeat detection."""
    f = _write(tmp_path / "bom.rtf", b"\xef\xbb\xbf" + rb"{\rtf1\ansi hi\par}")
    assert detect_format(f).content_type == CONTENT_TYPE_RTF


def test_plain_zip_is_rejected(tmp_path: Path) -> None:
    f = _write_zip(tmp_path / "a.zip", ["notes.txt"])
    with pytest.raises(UnsupportedFormat, match="OOXML"):
        detect_format(f)


def test_corrupt_zip_is_rejected(tmp_path: Path) -> None:
    """ZIP magic bytes but not a valid archive → clear error, not a crash."""
    f = _write(tmp_path / "a.docx", b"PK\x03\x04" + b"\x00" * 20)
    with pytest.raises(UnsupportedFormat, match="corrupt ZIP"):
        detect_format(f)


def test_extension_is_ignored_only_bytes_matter(tmp_path: Path) -> None:
    """A file named .docx that is really an xlsx detects as xlsx."""
    f = _write_zip(tmp_path / "misnamed.docx", ["xl/workbook.xml"])
    assert detect_format(f).content_type == CONTENT_TYPE_XLSX


def test_detects_pdf_digital(tmp_path: Path) -> None:
    f = _write(tmp_path / "a.pdf", b"%PDF-1.7\n1 0 obj<</Font 2 0 R>>endobj\n")
    result = detect_format(f)
    assert result.content_type == CONTENT_TYPE_PDF
    assert result.is_scanned_pdf is False


def test_pdf_image_only_hint_is_unknown_not_scanned(tmp_path: Path) -> None:
    """Image XObjects without a font are not proof of scanning → hint stays None."""
    f = _write(tmp_path / "a.pdf", b"%PDF-1.7\n1 0 obj<</XObject<</Im0 2 0 R>>>>endobj\n")
    result = detect_format(f)
    assert result.content_type == CONTENT_TYPE_PDF
    assert result.is_scanned_pdf is None


def test_detects_pdf_unknown_scan_hint(tmp_path: Path) -> None:
    f = _write(tmp_path / "a.pdf", b"%PDF-1.7\n")
    result = detect_format(f)
    assert result.content_type == CONTENT_TYPE_PDF
    assert result.is_scanned_pdf is None


def test_detects_ole2_legacy_office(tmp_path: Path) -> None:
    """Legacy .doc/.xls are OLE2 compound files; the engine resolves the exact kind."""
    f = _write(tmp_path / "a.doc", _OLE2_MAGIC + b"\x00" * 32)
    assert detect_format(f).content_type == CONTENT_TYPE_OLE2


def test_detects_ole2_regardless_of_embedded_streams(tmp_path: Path) -> None:
    """An OLE2 file is detected as OLE2 even when it embeds a marker of another kind."""
    data = _OLE2_MAGIC + b"\x00" * 16 + "WordDocument".encode("utf-16-le")
    f = _write(tmp_path / "a.xls", data)
    assert detect_format(f).content_type == CONTENT_TYPE_OLE2


def test_unknown_bytes_are_rejected(tmp_path: Path) -> None:
    f = _write(tmp_path / "a.txt", b"just some plain text")
    with pytest.raises(UnsupportedFormat, match="unrecognized format"):
        detect_format(f)


@pytest.mark.parametrize(
    ("magic", "content_type"),
    [
        (b"\x89PNG\r\n\x1a\n", CONTENT_TYPE_PNG),
        (b"\xff\xd8\xff\xe0" + b"\x00" * 8, CONTENT_TYPE_JPEG),
        (b"II*\x00" + b"\x00" * 8, CONTENT_TYPE_TIFF),  # little-endian TIFF
        (b"MM\x00*" + b"\x00" * 8, CONTENT_TYPE_TIFF),  # big-endian, as some scanners write
    ],
)
def test_page_images_are_detected(tmp_path: Path, magic: bytes, content_type: str) -> None:
    path = tmp_path / "scan.bin"
    path.write_bytes(magic)
    assert detect_format(path).content_type == content_type


def test_an_image_carries_no_scanned_pdf_hint(tmp_path: Path) -> None:
    # The hint is about a PDF's text layer. An image has none to have, so it stays unset
    # and the pipeline decides on OCR from the content type instead.
    path = tmp_path / "scan.png"
    path.write_bytes(b"\x89PNG\r\n\x1a\n")
    assert detect_format(path).is_scanned_pdf is None


def test_bmp_is_still_unsupported(tmp_path: Path) -> None:
    """Left out on purpose: a two-byte signature misfires on unrelated files, and BMP is
    not a format documents arrive in."""
    path = tmp_path / "image.bmp"
    path.write_bytes(b"BM" + b"\x00" * 10)
    with pytest.raises(UnsupportedFormat):
        detect_format(path)
