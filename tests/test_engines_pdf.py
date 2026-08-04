"""Tests for the digital PDF extraction adapter."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from viparse.detect import CONTENT_TYPE_PDF
from viparse.engines.pdf import PdfEngine, _table_rows
from viparse.errors import MissingDependency
from viparse.options import LoadOptions
from viparse.registry import EngineRegistry

pytest.importorskip("pdfplumber")  # skipped without the pdf extra
reportlab = pytest.importorskip("reportlab")  # dev-only: builds the synthetic fixtures


def _make_pdf(path: Path, *, table: bool = True, pages: int = 1) -> Path:
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    styles = getSampleStyleSheet()
    grid = TableStyle([("GRID", (0, 0), (-1, -1), 1, colors.black)])
    elements: list[object] = [Paragraph("Report body paragraph one.", styles["Normal"])]
    if table:
        elements += [Spacer(1, 12), Table([["Name", "Age"], ["An", "30"]], style=grid)]
    for _ in range(pages - 1):
        elements += [PageBreak(), Paragraph("Second page text.", styles["Normal"])]
    SimpleDocTemplate(str(path)).build(elements)
    return path


def test_extract_returns_raw_extraction(tmp_path: Path) -> None:
    raw = PdfEngine().extract(_make_pdf(tmp_path / "a.pdf"), LoadOptions())
    assert raw.engine == "pdf"
    assert raw.content_type == CONTENT_TYPE_PDF
    assert "Report body paragraph one." in raw.text


def test_body_paragraph_and_table_blocks(tmp_path: Path) -> None:
    raw = PdfEngine().extract(_make_pdf(tmp_path / "a.pdf"), LoadOptions())
    blocks = raw.signals["blocks"]
    assert [b["type"] for b in blocks] == ["paragraph", "table"]
    assert blocks[0]["text"] == "Report body paragraph one."
    assert blocks[1]["rows"] == [["Name", "Age"], ["An", "30"]]


def test_table_cells_are_not_duplicated_in_body_text(tmp_path: Path) -> None:
    raw = PdfEngine().extract(_make_pdf(tmp_path / "a.pdf"), LoadOptions())
    paragraph = next(b for b in raw.signals["blocks"] if b["type"] == "paragraph")
    assert "An" not in paragraph["text"]  # the table's cells stay out of the prose


def test_captures_font_signal(tmp_path: Path) -> None:
    raw = PdfEngine().extract(_make_pdf(tmp_path / "a.pdf"), LoadOptions())
    assert any("Helvetica" in font for font in raw.signals["fonts"])


def test_page_without_a_table_uses_direct_text(tmp_path: Path) -> None:
    raw = PdfEngine().extract(_make_pdf(tmp_path / "notable.pdf", table=False), LoadOptions())
    assert [b["type"] for b in raw.signals["blocks"]] == ["paragraph"]
    assert raw.page == 1


def test_multiple_pages_are_concatenated(tmp_path: Path) -> None:
    raw = PdfEngine().extract(
        _make_pdf(tmp_path / "multi.pdf", table=False, pages=2), LoadOptions()
    )
    assert "Report body paragraph one." in raw.text
    assert "Second page text." in raw.text
    assert raw.page is None  # multi-page → not a single-page provenance


def test_table_only_page_has_no_body_paragraph(tmp_path: Path) -> None:
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

    grid = TableStyle([("GRID", (0, 0), (-1, -1), 1, colors.black)])
    path = tmp_path / "tableonly.pdf"
    SimpleDocTemplate(str(path)).build([Table([["A", "B"], ["1", "2"]], style=grid)])
    raw = PdfEngine().extract(path, LoadOptions())
    assert [b["type"] for b in raw.signals["blocks"]] == ["table"]  # no body paragraph


def test_document_order_is_preserved_when_table_precedes_prose(tmp_path: Path) -> None:
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    grid = TableStyle([("GRID", (0, 0), (-1, -1), 1, colors.black)])
    path = tmp_path / "tablefirst.pdf"
    SimpleDocTemplate(str(path)).build(
        [
            Table([["A", "B"], ["1", "2"]], style=grid),
            Spacer(1, 12),
            Paragraph("Prose after the table.", styles["Normal"]),
        ]
    )
    raw = PdfEngine().extract(path, LoadOptions())
    assert [b["type"] for b in raw.signals["blocks"]] == ["table", "paragraph"]
    paragraph = next(b for b in raw.signals["blocks"] if b["type"] == "paragraph")
    assert "Prose after the table." in paragraph["text"]


def test_table_rows_maps_none_and_collapses_wrapped_cell_whitespace() -> None:
    class _FakeTable:
        @staticmethod
        def extract() -> list[list[str | None]]:
            return [[None, "So 12\nQuan 1"], ["Hà  Nội", None]]

    # None → ""; an intra-cell newline (wrapped text) collapses to a single space.
    assert _table_rows(_FakeTable()) == [["", "So 12 Quan 1"], ["Hà Nội", ""]]


def test_append_band_skips_a_zero_height_band() -> None:
    from viparse.engines.pdf import _append_band

    class _NoCropPage:
        width = 100.0
        height = 200.0

        def crop(self, bbox: object) -> object:
            raise AssertionError("a zero-height band must not be cropped")

    blocks: list[dict[str, object]] = []
    _append_band(_NoCropPage(), 50.0, 50.0, blocks)
    assert blocks == []


def test_supports_only_pdf() -> None:
    engine = PdfEngine()
    assert engine.supports(CONTENT_TYPE_PDF)
    assert not engine.supports("application/vnd.ms-excel")


def test_registry_selects_pdf_engine() -> None:
    reg = EngineRegistry()
    reg.register(PdfEngine())
    assert isinstance(reg.select(CONTENT_TYPE_PDF), PdfEngine)


def test_missing_dependency_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "pdfplumber", None)
    with pytest.raises(MissingDependency, match=r"viparse\[pdf\]"):
        PdfEngine().extract("missing.pdf", LoadOptions())


def _make_split_table_pdf(path: Path, *, rows: int = 60) -> Path:
    """A table long enough that the page break lands inside it."""
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    data = [["Name", "Age"]] + [[f"Person {i:02d}", str(20 + i)] for i in range(rows)]
    SimpleDocTemplate(str(path)).build(
        [
            Paragraph("Report body paragraph one.", styles["Normal"]),
            Spacer(1, 12),
            Table(data, style=TableStyle([("GRID", (0, 0), (-1, -1), 1, colors.black)])),
        ]
    )
    return path


def test_a_table_split_by_a_page_break_comes_back_as_one_block(tmp_path: Path) -> None:
    """Otherwise the continuation has no header row, and a chunk cut from it is bare data.

    Rows survive either way, which is why this went unnoticed: the failure is not missing
    text, it is text whose columns no longer have names.
    """
    raw = PdfEngine().extract(_make_split_table_pdf(tmp_path / "long.pdf"), LoadOptions())
    tables = [b for b in raw.signals["blocks"] if b["type"] == "table"]
    assert len(tables) == 1
    assert tables[0]["rows"][0] == ["Name", "Age"]
    assert tables[0]["rows"][-1] == ["Person 59", "79"]
    assert len(tables[0]["rows"]) == 61  # header + 60 data rows, none lost to the join


def test_two_tables_on_one_page_are_not_joined(tmp_path: Path) -> None:
    # Only a table that opens a page can continue a previous one; two tables separated by
    # prose on the same page are two tables.
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    grid = TableStyle([("GRID", (0, 0), (-1, -1), 1, colors.black)])
    SimpleDocTemplate(str(tmp_path / "two.pdf")).build(
        [
            Table([["Name", "Age"], ["An", "30"]], style=grid),
            Spacer(1, 12),
            Paragraph("Between the tables.", styles["Normal"]),
            Spacer(1, 12),
            Table([["City", "Pop"], ["Huế", "5"]], style=grid),
        ]
    )
    raw = PdfEngine().extract(tmp_path / "two.pdf", LoadOptions())
    tables = [b for b in raw.signals["blocks"] if b["type"] == "table"]
    assert [t["rows"][0] for t in tables] == [["Name", "Age"], ["City", "Pop"]]


def test_a_new_table_below_prose_on_a_later_page_is_not_joined(tmp_path: Path) -> None:
    # The page after the split starts with text, so its table is a new one.
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    styles = getSampleStyleSheet()
    grid = TableStyle([("GRID", (0, 0), (-1, -1), 1, colors.black)])
    SimpleDocTemplate(str(tmp_path / "sep.pdf")).build(
        [
            Table([["Name", "Age"], ["An", "30"]], style=grid),
            PageBreak(),
            Paragraph("A heading-ish line on page two.", styles["Normal"]),
            Spacer(1, 12),
            Table([["City", "Pop"], ["Huế", "5"]], style=grid),
        ]
    )
    raw = PdfEngine().extract(tmp_path / "sep.pdf", LoadOptions())
    tables = [b for b in raw.signals["blocks"] if b["type"] == "table"]
    assert len(tables) == 2
