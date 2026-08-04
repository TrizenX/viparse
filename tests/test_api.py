"""Tests for the public load / load_batch API (extract → normalize → render, end to end)."""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import pytest

import viparse
from viparse import load, load_batch
from viparse.model import Document

docx = pytest.importorskip("docx")  # python-docx; skipped without the office extra


def _write_docx(path: Path, text: str, font: str | None = None) -> Path:
    document = docx.Document()
    run = document.add_paragraph().add_run(text)
    if font is not None:
        run.font.name = font
    document.save(str(path))
    return path


def test_load_returns_single_document_list_in_nfc(tmp_path: Path) -> None:
    path = _write_docx(tmp_path / "a.docx", "Tiếng Việt")
    result = load(path)
    assert isinstance(result, list) and len(result) == 1
    doc = result[0]
    assert isinstance(doc, Document)
    assert doc.text == "Tiếng Việt"  # markdown default: a lone paragraph is plain text
    assert unicodedata.is_normalized("NFC", doc.text)
    assert doc.metadata.engine == "docx"


def test_load_output_json(tmp_path: Path) -> None:
    path = _write_docx(tmp_path / "a.docx", "Xin chào")
    (doc,) = load(path, output="json")
    payload = json.loads(doc.text)
    assert payload["schema_version"] == "1.0"
    assert payload["blocks"] == [{"type": "paragraph", "text": "Xin chào"}]


def test_load_encoding_override_converts_legacy(tmp_path: Path) -> None:
    # TCVN3 surface bytes rendered with a legacy font; forcing the encoding converts them.
    path = _write_docx(tmp_path / "legacy.docx", "µ¸¶·¹", font=".VnTime")
    (doc,) = load(path, output="text", encoding="tcvn3")
    assert doc.text == "àáảãạ"
    assert doc.metadata.encoding_detected == "tcvn3"


def test_load_respects_normalize_form(tmp_path: Path) -> None:
    path = _write_docx(tmp_path / "a.docx", "Việt")
    (doc,) = load(path, output="text", normalize="NFD")
    assert doc.text == unicodedata.normalize("NFD", "Việt")
    assert not unicodedata.is_normalized("NFC", doc.text)


def test_load_batch_is_lazy_and_yields_per_source(tmp_path: Path) -> None:
    a = _write_docx(tmp_path / "a.docx", "Một")
    b = _write_docx(tmp_path / "b.docx", "Hai")
    batch = load_batch([a, b], output="text")
    assert iter(batch) is batch  # a generator, not a materialized list
    results = list(batch)
    assert [r[0].text for r in results] == ["Một", "Hai"]


def test_load_rejects_oversized_input(tmp_path: Path) -> None:
    from viparse.errors import UnsafeInput

    path = _write_docx(tmp_path / "a.docx", "Xin chào")
    with pytest.raises(UnsafeInput):
        load(path, max_bytes=10)


def test_load_cache_hit_skips_parsing(tmp_path: Path) -> None:
    from viparse import MemoryCache
    from viparse.cache import cache_key
    from viparse.model import Document, DocumentMetadata
    from viparse.options import LoadOptions

    path = _write_docx(tmp_path / "a.docx", "real content")
    cache = MemoryCache()
    sentinel = Document(text="FROM CACHE", metadata=DocumentMetadata(source="x", content_type="y"))
    cache.set(cache_key(path, LoadOptions()), sentinel)  # LoadOptions() matches load() defaults
    (doc,) = load(path, cache=cache)
    assert doc.text == "FROM CACHE"  # returned the cache, never parsed "real content"


def test_load_populates_cache_on_miss(tmp_path: Path) -> None:
    from viparse import MemoryCache
    from viparse.cache import cache_key
    from viparse.options import LoadOptions

    path = _write_docx(tmp_path / "a.docx", "Tài liệu")
    cache = MemoryCache()
    (doc,) = load(path, cache=cache)
    assert doc.text == "Tài liệu"
    assert cache.get(cache_key(path, LoadOptions())) is doc


def test_load_batch_isolates_a_failing_source(tmp_path: Path) -> None:
    good = _write_docx(tmp_path / "a.docx", "ok")
    bad = tmp_path / "bad.txt"
    bad.write_text("not a document", encoding="utf-8")
    results = list(load_batch([good, bad], output="text"))
    assert results[0][0].text == "ok"
    assert results[1][0].text == ""  # the failure was isolated, not raised
    assert results[1][0].metadata.warnings  # and recorded


def test_load_batch_parallel_matches_sequential_order(tmp_path: Path) -> None:
    paths = [_write_docx(tmp_path / f"{i}.docx", f"doc {i}") for i in range(6)]
    sequential = [r[0].text for r in load_batch(paths, output="text")]
    parallel = [r[0].text for r in load_batch(paths, output="text", workers=3)]
    assert parallel == sequential == [f"doc {i}" for i in range(6)]


def test_load_batch_parallel_isolates_failures(tmp_path: Path) -> None:
    good = _write_docx(tmp_path / "a.docx", "ok")
    bad = tmp_path / "bad.txt"
    bad.write_text("x", encoding="utf-8")
    # workers (3) > sources (2) exercises the priming break as well.
    results = list(load_batch([good, bad], output="text", workers=3))
    assert results[0][0].text == "ok"
    assert results[1][0].metadata.warnings


def test_load_batch_error_entry_is_valid_json(tmp_path: Path) -> None:
    import json

    good = _write_docx(tmp_path / "a.docx", "Xin chào")
    bad = tmp_path / "bad.txt"
    bad.write_text("x", encoding="utf-8")
    results = list(load_batch([good, bad], output="json"))
    json.loads(results[0][0].text)  # the good one
    error = json.loads(results[1][0].text)  # must be valid JSON, not ""
    assert error["blocks"] == []
    assert any("failed to load" in w for w in error["warnings"])


def test_load_batch_isolates_a_missing_file(tmp_path: Path) -> None:
    good = _write_docx(tmp_path / "a.docx", "ok")
    results = list(load_batch([good, tmp_path / "ghost.docx"], output="text"))
    assert results[0][0].text == "ok"
    assert results[1][0].metadata.warnings  # OSError isolated, not raised


# --- fix(): the normalization pass, without a file (VIP-117) --------------------------


def test_fix_repairs_text_another_tool_extracted() -> None:
    """The pass the README always described and the API did not offer.

    Reaching it meant constructing a RawExtraction and a LoadOptions and calling the
    normalizer — four places in this project did exactly that, including its own MCP
    server and its own agent skill.
    """
    assert viparse.fix("B¸o c¸o tµi chÝnh") == "Báo cáo tài chính"
    assert viparse.fix("Coäng hoøa xaõ hoäi chuû nghóa") == "Cộng hòa xã hội chủ nghĩa"


def test_fix_leaves_text_that_is_already_right_alone() -> None:
    """Never corrupt good text — including when the good text is not Vietnamese."""
    for text in (
        "Đã là Unicode rồi, không cần sửa gì",
        "Señor Muñoz vivía en la mañana con niños pequeños en España",
        "An ordinary English sentence with nothing unusual in it.",
    ):
        assert viparse.fix(text) == text


def test_fix_takes_a_named_encoding_when_detection_gets_a_fragment_wrong() -> None:
    """Detection scores character frequencies, and a fragment gives it little to score.

    `laäp` is VNI for lập and comes back as VISCII's reading. Four characters are not
    enough to separate two tables that both find *some* Vietnamese in them. Naming the
    encoding is the answer when the source is known, which is the case whenever this is
    used as a pass over one loader's output.
    """
    assert viparse.fix("laäp") != "lập"
    assert viparse.fix("laäp", encoding="vni") == "lập"


def test_detect_text_encoding_names_it_without_changing_anything() -> None:
    assert viparse.detect_text_encoding("Coäng hoøa xaõ hoäi chuû nghóa Vieät Nam") == "vni"
    assert viparse.detect_text_encoding("B¸o c¸o tµi chÝnh quý II n¨m 2008") == "tcvn3"


def test_detect_text_encoding_returns_none_for_text_it_should_not_touch() -> None:
    """One `None` covers already-Unicode and actively-not-Vietnamese alike.

    A caller treats both the same way: leave it alone. Note what is *not* in this list —
    a short fragment. There is no length floor at document level, so `lËp` detects as
    TCVN3 and converts; the floor that rejects fragments lives in the per-block path,
    where a spreadsheet cell would otherwise be judged on nothing.
    """
    for text in (
        "Cộng hòa xã hội chủ nghĩa Việt Nam",
        "Señor Muñoz vivía en la mañana con niños pequeños en España",
    ):
        assert viparse.detect_text_encoding(text) is None
