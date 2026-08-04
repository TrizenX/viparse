"""Tests for the OCR adapter — scanned PDFs and page images.

The external OCR stack (pytesseract/pdf2image + the Tesseract/poppler binaries) is
mocked so the adapter logic is covered deterministically without those heavy, non-pip
dependencies. Page images are real Pillow images, so the preprocessing runs for real.

**What this does not establish.** Every assertion here is against a mock: these tests show
the adapter is wired correctly, not that OCR is accurate. Accuracy is measured separately,
in viparse-corpus (``ocr/README.md``) — 0.967 diacritic on rendered prose, 0.898 on
degraded pages, against 0.982 for the conversion path.

Sources are real files on disk, because the engine re-detects the content type it is
reading and cannot be handed a bare string.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest
from PIL import Image

from viparse.detect import CONTENT_TYPE_JPEG, CONTENT_TYPE_PDF, CONTENT_TYPE_PNG, CONTENT_TYPE_TIFF
from viparse.engines.ocr import OcrEngine
from viparse.errors import ExtractionError, MissingDependency
from viparse.options import LoadOptions


class _TesseractNotFound(Exception):
    pass


class _PDFInfoNotInstalled(Exception):
    pass


def _pdf(tmp_path: Path) -> Path:
    """The smallest thing `detect_format` calls a PDF; rasterizing it is mocked away."""
    path = tmp_path / "scan.pdf"
    path.write_bytes(b"%PDF-1.4\n")
    return path


def _image(tmp_path: Path, fmt: str, *, frames: int = 1) -> Path:
    """A real image file — Pillow opens this one for real, only the OCR call is mocked."""
    suffix = {"PNG": "png", "JPEG": "jpg", "TIFF": "tif"}[fmt]
    path = tmp_path / f"scan.{suffix}"
    pages = [Image.new("RGB", (16, 16), "white") for _ in range(frames)]
    pages[0].save(path, format=fmt, save_all=frames > 1, append_images=pages[1:])
    return path


def _page(words_and_confs: list[tuple[str, int]]) -> dict[str, list]:
    """A pytesseract image_to_data DICT for one page (parallel text/conf lists)."""
    return {
        "text": [word for word, _ in words_and_confs],
        "conf": [conf for _, conf in words_and_confs],
    }


def _install(
    monkeypatch: pytest.MonkeyPatch,
    *,
    pages: list[dict[str, list]] | None = None,
    convert_error: Exception | None = None,
    data_error: Exception | None = None,
) -> None:
    calls = {"i": 0}

    def image_to_data(
        image: object, lang: str, timeout: int, output_type: object
    ) -> dict[str, list]:
        if data_error is not None:
            raise data_error
        assert pages is not None
        page = pages[calls["i"]]
        calls["i"] += 1
        return page

    pytesseract = types.SimpleNamespace(
        image_to_data=image_to_data,
        Output=types.SimpleNamespace(DICT="dict"),
        TesseractNotFoundError=_TesseractNotFound,
    )

    def convert_from_path(path: str, dpi: int) -> list[Image.Image]:
        if convert_error is not None:
            raise convert_error
        count = len(pages) if pages is not None else 1
        return [Image.new("RGB", (8, 8), "white") for _ in range(count)]

    pdf2image = types.SimpleNamespace(
        convert_from_path=convert_from_path,
        exceptions=types.SimpleNamespace(PDFInfoNotInstalledError=_PDFInfoNotInstalled),
    )
    monkeypatch.setitem(sys.modules, "pytesseract", pytesseract)
    monkeypatch.setitem(sys.modules, "pdf2image", pdf2image)


def test_extract_ocrs_pages_into_blocks(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _install(monkeypatch, pages=[_page([("Tiếng", 95), ("Việt", 90), ("", -1)])])
    raw = OcrEngine().extract(_pdf(tmp_path), LoadOptions())
    assert raw.engine == "ocr"
    assert raw.content_type == CONTENT_TYPE_PDF
    assert raw.signals["blocks"] == [{"type": "paragraph", "text": "Tiếng Việt"}]
    assert raw.signals["fonts"] == []  # OCR output carries no legacy font signal
    assert raw.warnings == []


def test_low_confidence_pages_warn(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _install(monkeypatch, pages=[_page([("mờ", 40), ("nhòe", 45)])])
    raw = OcrEngine().extract(_pdf(tmp_path), LoadOptions())
    assert raw.text == "mờ nhòe"
    assert any("confidence" in w for w in raw.warnings)


def test_blank_words_with_confidence_are_dropped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Tesseract can report a whitespace token with a real confidence; it counts toward
    # the confidence average but must not appear in the text.
    _install(monkeypatch, pages=[_page([("Có", 95), ("   ", 80)])])
    raw = OcrEngine().extract(_pdf(tmp_path), LoadOptions())
    assert raw.signals["blocks"] == [{"type": "paragraph", "text": "Có"}]


def test_empty_pages_are_skipped(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _install(
        monkeypatch,
        pages=[_page([("Trang", 88)]), _page([("", -1), ("  ", -1)])],
    )
    raw = OcrEngine().extract(_pdf(tmp_path), LoadOptions())
    assert raw.signals["blocks"] == [{"type": "paragraph", "text": "Trang"}]


def test_missing_python_libraries_raise(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setitem(sys.modules, "pytesseract", None)
    with pytest.raises(MissingDependency, match=r"viparse\[ocr\]"):
        OcrEngine().extract(_pdf(tmp_path), LoadOptions())


def test_missing_tesseract_binary_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _install(monkeypatch, pages=[_page([("x", 90)])], data_error=_TesseractNotFound())
    with pytest.raises(MissingDependency, match=r"tesseract-ocr"):
        OcrEngine().extract(_pdf(tmp_path), LoadOptions())


def test_missing_poppler_binary_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _install(monkeypatch, convert_error=_PDFInfoNotInstalled())
    with pytest.raises(MissingDependency, match=r"poppler"):
        OcrEngine().extract(_pdf(tmp_path), LoadOptions())


def test_ocr_timeout_raises_extraction_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # pytesseract raises RuntimeError on the per-page Tesseract timeout.
    _install(monkeypatch, pages=[_page([("x", 90)])], data_error=RuntimeError("Tesseract timeout"))
    with pytest.raises(ExtractionError, match="timed out"):
        OcrEngine().extract(_pdf(tmp_path), LoadOptions())


def test_supports_pdf_and_page_images() -> None:
    engine = OcrEngine()
    assert engine.supports(CONTENT_TYPE_PDF)
    assert engine.supports(CONTENT_TYPE_PNG)
    assert engine.supports(CONTENT_TYPE_JPEG)
    assert engine.supports(CONTENT_TYPE_TIFF)
    assert not engine.supports(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


def test_marks_output_native_unicode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # So the normalizer skips encoding detection (OCR output is already Unicode).
    _install(monkeypatch, pages=[_page([("chào", 90)])])
    raw = OcrEngine().extract(_pdf(tmp_path), LoadOptions())
    assert raw.signals["native_unicode"] is True


def test_is_marked_as_an_ocr_engine() -> None:
    # The pipeline keys off this to run OCR only when options.ocr is True.
    assert OcrEngine.ocr is True


@pytest.mark.parametrize(
    ("fmt", "content_type"),
    [("PNG", CONTENT_TYPE_PNG), ("JPEG", CONTENT_TYPE_JPEG), ("TIFF", CONTENT_TYPE_TIFF)],
)
def test_page_image_is_ocrd(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fmt: str, content_type: str
) -> None:
    _install(monkeypatch, pages=[_page([("Tiếng", 95), ("Việt", 90)])])
    raw = OcrEngine().extract(_image(tmp_path, fmt), LoadOptions())
    assert raw.engine == "ocr"
    # The result names the format it actually read, not the PDF it used to assume.
    assert raw.content_type == content_type
    assert raw.text == "Tiếng Việt"
    assert raw.signals["native_unicode"] is True


def test_multi_page_tiff_yields_one_block_per_frame(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A digitised archive is one TIFF holding many pages; reading only the first
    would drop the rest without a word."""
    _install(
        monkeypatch,
        pages=[_page([("trang", 90), ("một", 90)]), _page([("trang", 90), ("hai", 90)])],
    )
    raw = OcrEngine().extract(_image(tmp_path, "TIFF", frames=2), LoadOptions())
    assert [b["text"] for b in raw.signals["blocks"]] == ["trang một", "trang hai"]


def test_image_ocr_does_not_need_pdf2image(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Poppler is the harder binary to install and has nothing to rasterize here.

    pdf2image is removed from sys.modules and blocked from importing; a page image must
    still OCR, which is the whole point of splitting the two dependencies.
    """
    _install(monkeypatch, pages=[_page([("ảnh", 90)])])
    monkeypatch.delitem(sys.modules, "pdf2image", raising=False)
    monkeypatch.setattr(
        "viparse.engines.ocr._import_pdf2image",
        lambda: pytest.fail("a page image must not require pdf2image"),
    )
    raw = OcrEngine().extract(_image(tmp_path, "PNG"), LoadOptions())
    assert raw.text == "ảnh"


def test_unreadable_image_raises_extraction_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Correct magic bytes, nothing behind them — the router says PNG, Pillow disagrees.
    _install(monkeypatch, pages=[_page([("x", 90)])])
    path = tmp_path / "truncated.png"
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)
    with pytest.raises(ExtractionError, match="could not read image"):
        OcrEngine().extract(path, LoadOptions())
