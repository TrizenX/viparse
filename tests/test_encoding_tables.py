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


# Words quoted from the VNI documents in TrizenX/viparse-corpus, with the reading a
# person gave them. Unlike the parametrised test above — which asserts the table equals
# itself and passes whatever the table says — these fail if a sequence is wrong.
#
# This is how `a½` survived: it is a TCVN3 byte (0xBD is ẵ there), it appears in no VNI
# document, and a self-referential test cannot notice an entry that never matches.
_VNI_SURFACE_FORMS_FROM_REAL_DOCUMENTS = [
    ("thaønh", "thành"),
    ("ngaønh", "ngành"),
    ("baøn", "bàn"),
    ("Caø Mau", "Cà Mau"),
]


@pytest.mark.parametrize(("surface", "expected"), _VNI_SURFACE_FORMS_FROM_REAL_DOCUMENTS)
def test_vni_converts_words_taken_from_real_documents(surface: str, expected: str) -> None:
    assert convert(surface, _VNI) == unicodedata.normalize("NFC", expected)


# The four letters the table deliberately does not map, and why a test names them:
# an absent entry is indistinguishable from a forgotten one unless something records
# the difference. If a VNI document containing one of these is ever collected, this
# test is the thing that should fail.
_VNI_KNOWN_GAPS = ["ẳ", "Ẳ"]


@pytest.mark.parametrize("letter", _VNI_KNOWN_GAPS)
def test_vni_gap_is_deliberate_and_unmapped(letter: str) -> None:
    assert letter not in {target for _, target in _VNI.pairs}


def test_vni_covers_the_vietnamese_repertoire_apart_from_the_known_gaps() -> None:
    """Every Vietnamese accented letter except the four unobserved ones.

    The table is generated from the corpus by inverting a decoding table, and an
    inversion can produce letters Vietnamese does not have — an earlier pass emitted
    `ĕ`, `ĭ`, `ŏ`, `ŭ`, `ŷ` because they compose to a single codepoint and nothing
    checked they were Vietnamese. This asserts the repertoire in both directions.
    """
    accented = "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
    repertoire = set(accented) | {ch.upper() for ch in accented}
    mapped = {target for _, target in _VNI.pairs}
    assert mapped - repertoire == set(), "table maps non-Vietnamese letters"
    assert repertoire - mapped == set(_VNI_KNOWN_GAPS)


# Whole phrases quoted from the VNI documents in viparse-corpus. Words alone exercise a
# handful of entries; these are the fixed formulas every Vietnamese administrative
# document opens with, and they run the base+mark machinery over both cases at once.
_VNI_PHRASES_FROM_REAL_DOCUMENTS = [
    ("COÄNG HOØA XAÕ HOÄI CHUÛ NGHÓA VIEÄT NAM", "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM"),
    ("Ñoäc laäp - Töï do - Haïnh phuùc", "Độc lập - Tự do - Hạnh phúc"),
    ("UÛY BAN NHAÂN DAÂN TÆNH", "ỦY BAN NHÂN DÂN TỈNH"),
    ("Caên cöù Luaät Toå chöùc HÑND vaø UBND", "Căn cứ Luật Tổ chức HĐND và UBND"),
    ("quyeát ñònh naøy coù hieäu löïc", "quyết định này có hiệu lực"),
    ("nghæ maát söùc", "nghỉ mất sức"),
    # ẵ. Invisible until the mixed-encoding Lâm Đồng document got a transcript — both
    # occurrences in the whole corpus sit in the one file nobody could read.
    ("saün coù", "sẵn có"),
    ("Ñaø Naüng", "Đà Nẵng"),
]


@pytest.mark.parametrize(("surface", "expected"), _VNI_PHRASES_FROM_REAL_DOCUMENTS)
def test_vni_converts_phrases_taken_from_real_documents(surface: str, expected: str) -> None:
    assert convert(surface, _VNI) == unicodedata.normalize("NFC", expected)


def test_vni_table_holds_no_sequence_absent_from_real_documents() -> None:
    """`½` is TCVN3's ẵ and has no role in VNI.

    Narrow on purpose. It guards the specific byte that was wrong rather than asserting
    something general about which characters VNI may use, which would need an
    authoritative charset file this table does not yet have.
    """
    assert not [pair for pair in _VNI.pairs if "\u00bd" in pair[0]]


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


# --- Glyph substitutions a PDF text layer makes (VIP-105) -----------------------------

# Words quoted from the legacy PDFs in viparse-corpus, with the reading a person gives
# them. U+2212 stands where TCVN3 has 0xAD (ư) and U+2219 where it has 0xB7 (ã), because
# a PDF stores glyph codes and the extractor resolves them through the font's encoding.
_PDF_SUBSTITUTED = [
    ("nhµ n−íc", "nhà nước"),
    ("Thñ t−íng", "Thủ tướng"),
    ("Th«ng t−", "Thông tư"),
    ("céng hoµ x∙ héi", "cộng hoà xã hội"),
    ("Quü b¶o l∙nh", "Quỹ bảo lãnh"),
]


@pytest.mark.parametrize(("surface", "expected"), _PDF_SUBSTITUTED)
def test_pdf_glyph_substitutions_are_restored(surface: str, expected: str) -> None:
    """The third mechanism by which ư goes missing.

    A legacy `.doc` lost it through `<w:softHyphen/>`; a PDF loses it here. 129
    occurrences across the five legacy PDFs in the corpus, every one a letter.
    """
    assert convert(surface, _TCVN3) == unicodedata.normalize("NFC", expected)


def test_a_minus_sign_between_digits_is_left_alone() -> None:
    """Adjacency decides, and it has to.

    These documents are statistics tables. Restoring every U+2212 would turn a real
    minus into ư and corrupt the numbers — trading one silent loss for another.
    """
    assert convert("t¨ng 5 − 3 phÇn tr¨m", _TCVN3) == "tăng 5 − 3 phần trăm"


def test_substitutions_only_apply_during_legacy_conversion() -> None:
    """Unicode text never reaches this code, because `convert` is not called on it.

    Asserted at the seam rather than assumed: a minus sign in an already-Unicode
    document must survive whatever this module does.
    """
    text = "Chỉ số tăng 5 − 3 điểm"
    assert "−" in text
    # No charmap is applied to Unicode, so the only way to reach `convert` is to ask for
    # it explicitly — and even then, the digits protect the sign.
    assert convert(text, _TCVN3) == text
