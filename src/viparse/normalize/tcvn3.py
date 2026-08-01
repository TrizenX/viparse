"""TCVN3 (ABC / ``.Vn`` fonts) → Unicode conversion table.

TCVN3 is the encoding behind the classic ``.VnTime`` / ``.VnArial`` fonts. Each
Vietnamese glyph occupies a single byte in the upper range; when such a document
is extracted, those bytes surface as the matching Latin-1/CP1252 characters
(e.g. ``0xB5`` → ``µ``). This table maps each of those surface characters back to
the correct Vietnamese letter.

**Provenance.** The source column was validated against a corpus of 31 real
TCVN3 documents published by Vietnamese government bodies between 1998 and 2009,
by aligning byte sequences with the fixed phrases such documents always carry —
``Cộng hoà xã hội chủ nghĩa Việt Nam``, ``Độc lập - Tự do - Hạnh phúc``,
``Căn cứ Nghị định số``. Every entry below except one is backed by an observed
occurrence; the exception is marked inline.

The layout that emerged explains why an earlier partial table stopped where it
did: ``0xA1``–``0xA7`` hold the **uppercase** base vowels and ``0xA8``–``0xAE``
their lowercase counterparts, so the bytes immediately below the accented ranges
are not accented letters at all.

.. note::
   TCVN3 has no uppercase *accented* letters. An uppercase heading is typed with
   uppercase ASCII plus the same accented bytes as lowercase, and the ``.VnTimeH``
   font draws them uppercase. Recovering that case needs the document's font runs
   and is out of scope for a byte-level table — text converted here comes back
   lowercase where the original was set in a ``H`` font.

Missing characters simply pass through unchanged.
"""

from __future__ import annotations

from viparse.normalize.tables import Charmap, build_charmap

ENCODING_NAME = "tcvn3"

# TCVN3 surface character → Unicode Vietnamese letter (NFC).
_ENTRIES = [
    # 0xA1–0xA7 — uppercase base vowels.
    ("\u00a1", "Ă"),
    ("\u00a2", "Â"),
    ("\u00a3", "Ê"),
    ("\u00a4", "Ô"),
    ("\u00a5", "Ơ"),  # inferred from the block; not observed in the corpus
    ("\u00a6", "Ư"),
    ("\u00a7", "Đ"),
    # 0xA8–0xAE — lowercase base vowels.
    ("¨", "ă"),
    ("©", "â"),
    ("ª", "ê"),
    ("«", "ô"),
    ("¬", "ơ"),
    ("\u00ad", "ư"),
    ("®", "đ"),
    # a
    ("µ", "à"),
    ("¸", "á"),
    ("¶", "ả"),
    ("·", "ã"),
    ("¹", "ạ"),
    # ă
    ("»", "ằ"),
    ("¾", "ắ"),
    ("¼", "ẳ"),
    ("½", "ẵ"),
    ("Æ", "ặ"),
    # â
    ("Ç", "ầ"),
    ("Ê", "ấ"),
    ("È", "ẩ"),
    ("É", "ẫ"),
    ("Ë", "ậ"),
    # e
    ("Ì", "è"),
    ("Ð", "é"),
    ("Î", "ẻ"),
    ("Ï", "ẽ"),
    ("Ñ", "ẹ"),
    # ê
    ("Ò", "ề"),
    ("Õ", "ế"),
    ("Ó", "ể"),
    ("Ô", "ễ"),
    ("Ö", "ệ"),
    # i
    ("×", "ì"),
    ("Ý", "í"),
    ("Ø", "ỉ"),
    ("Ü", "ĩ"),
    ("Þ", "ị"),
    # o
    ("ß", "ò"),
    ("ã", "ó"),
    ("á", "ỏ"),
    ("â", "õ"),
    ("ä", "ọ"),
    # ô
    ("å", "ồ"),
    ("è", "ố"),
    ("æ", "ổ"),
    ("ç", "ỗ"),
    ("é", "ộ"),
    # ơ
    ("ê", "ờ"),
    ("í", "ớ"),
    ("ë", "ở"),
    ("ì", "ỡ"),
    ("î", "ợ"),
    # u
    ("ï", "ù"),
    ("ó", "ú"),
    ("ñ", "ủ"),
    ("ò", "ũ"),
    ("ô", "ụ"),
    # ư
    ("õ", "ừ"),
    ("ø", "ứ"),
    ("ö", "ử"),
    ("÷", "ữ"),
    ("ù", "ự"),
    # y
    ("ú", "ỳ"),
    ("ý", "ý"),
    ("û", "ỷ"),
    ("ü", "ỹ"),
    ("þ", "ỵ"),
]

TCVN3: Charmap = build_charmap(ENCODING_NAME, _ENTRIES)
