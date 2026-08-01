"""Character-level regression tests over the legacy encoding tables (SPEC-6 E6.2 / T6.2.1).

Every conversion-table mapping is exercised entry-by-entry so a regression in any single
character fails loudly. (The NFD↔NFC repertoire round-trip lives in
``test_normalizer.py::test_nfc_nfd_roundtrip_for_all_accented_vowels``, which owns the single
source of truth for the Vietnamese letter set.)
"""

from __future__ import annotations

import unicodedata

import pytest

from viparse.normalize.detector import detect_encoding_by_content
from viparse.normalize.encodings import CHARMAPS
from viparse.normalize.tables import convert
from viparse.normalize.viscii import _BYTE_TO_CODEPOINT
from viparse.normalize.vps import _BYTE_TO_CODEPOINT as _VPS_BYTE_TO_CODEPOINT

_TCVN3 = CHARMAPS["tcvn3"]
_VNI = CHARMAPS["vni"]
_VISCII = CHARMAPS["viscii"]
_VPS = CHARMAPS["vps"]


# --- T6.2.1: every table entry converts to the correct NFC character -----------------


@pytest.mark.parametrize(("byte", "codepoint"), _BYTE_TO_CODEPOINT)
def test_viscii_entry_converts(byte: int, codepoint: int) -> None:
    assert convert(chr(byte), _VISCII) == unicodedata.normalize("NFC", chr(codepoint))


@pytest.mark.parametrize(("byte", "codepoint"), _VPS_BYTE_TO_CODEPOINT)
def test_vps_entry_converts(byte: int, codepoint: int) -> None:
    assert convert(chr(byte), _VPS) == unicodedata.normalize("NFC", chr(codepoint))


@pytest.mark.parametrize(("source", "target"), _TCVN3.pairs)
def test_tcvn3_entry_converts(source: str, target: str) -> None:
    assert convert(source, _TCVN3) == unicodedata.normalize("NFC", target)


@pytest.mark.parametrize(("source", "target"), _VNI.pairs)
def test_vni_entry_converts(source: str, target: str) -> None:
    assert convert(source, _VNI) == unicodedata.normalize("NFC", target)


@pytest.mark.parametrize("name", ["tcvn3", "vni", "viscii", "vps"])
def test_all_table_targets_are_nfc(name: str) -> None:
    assert all(unicodedata.is_normalized("NFC", target) for _, target in CHARMAPS[name].pairs)


# --- T6.2.3: content detection is a no-op on short / non-legacy strings ---------------


@pytest.mark.parametrize("text", ["", "a", "Hi", "ok then"])
def test_short_non_legacy_text_is_left_unconverted(text: str) -> None:
    assert detect_encoding_by_content(text, CHARMAPS).encoding is None


# --- TCVN3 against real documents ------------------------------------------------------

# Phrases lifted verbatim from Vietnamese government documents published 1998–2009, with
# their correct reading. A per-entry test proves each mapping in isolation; these prove the
# table converts running text, which is what caught the table being one sixth complete —
# every one of its twelve entries passed its own test while `chÝnh` still came out `chÝnh`.
_TCVN3_REAL = [
    ("Céng hoµ x· héi chñ nghÜa ViÖt Nam", "Cộng hoà xã hội chủ nghĩa Việt Nam"),
    ("§éc lËp - Tù do - H¹nh phóc", "Độc lập - Tự do - Hạnh phúc"),
    ("C¨n cø NghÞ ®Þnh sè 15/CP", "Căn cứ Nghị định số 15/CP"),
    ("quyÕt ®Þnh cña Bé tr\u00adëng Bé Tµi chÝnh", "quyết định của Bộ trưởng Bộ Tài chính"),
    ("chÕ ®é kÕ to¸n doanh nghiÖp", "chế độ kế toán doanh nghiệp"),
    ("ng\u00adêi cã c«ng víi c¸ch m¹ng", "người có công với cách mạng"),
    ("Tæng diÖn tÝch ®· phñ kÝn", "Tổng diện tích đã phủ kín"),
    ("§Ò nghÞ h\u00adëng trî cÊp mét lÇn", "Đề nghị hưởng trợ cấp một lần"),
    ("Th«ng t\u00ad h\u00adíng dÉn thùc hiÖn", "Thông tư hướng dẫn thực hiện"),
    ("§¡NG Ký KINH DOANH", "ĐĂNG KÝ KINH DOANH"),
    ("Trung ¢u", "Trung Âu"),
    ("¤ng TrÇn Du", "Ông Trần Du"),
]


@pytest.mark.parametrize(("legacy", "expected"), _TCVN3_REAL)
def test_tcvn3_converts_real_document_text(legacy: str, expected: str) -> None:
    # Uppercase accented letters need the document's font runs and are out of scope for a
    # byte table, so case is compared insensitively — the letters must all be right.
    assert convert(legacy, _TCVN3).lower() == unicodedata.normalize("NFC", expected).lower()


# Vietnamese letters that legitimately live in the Latin-1 supplement. Anything else in
# that range surviving a conversion is an unmapped byte, not an output character.
_VALID_LATIN1_VN = set("ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúý")


def test_tcvn3_leaves_no_latin1_residue() -> None:
    """No unmapped high byte survives conversion of real text.

    A leftover Latin-1 character is the signature of a gap in the table: the byte had no
    entry, so it passed through and would reach a vector database as mojibake. The check
    excludes the Vietnamese letters that genuinely live in that range — à á â ã and the
    rest are correct output, not residue.
    """
    for legacy, _ in _TCVN3_REAL:
        converted = convert(legacy, _TCVN3)
        residue = {ch for ch in converted if 0xA0 < ord(ch) < 0x100 and ch not in _VALID_LATIN1_VN}
        assert not residue, f"unmapped after conversion of {legacy!r}: {sorted(residue)}"
