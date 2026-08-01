"""VNI (VNI-Windows / ``VNI-Times`` fonts) → Unicode conversion table.

VNI is a **composite** encoding: a toned Vietnamese vowel is stored as a base
Latin letter followed by one or two mark characters from the upper byte range.
When extracted, those surface as a base letter plus the matching Latin-1/CP1252
characters, so the conversion sequences here are multi-character (e.g. ``a`` +
mark → ``á``). The framework matches longest sequences first, so ``aù`` is
converted before a bare ``a`` is ever considered.

.. warning::
   **Provenance.** Most of this table was transcribed from the standard VNI-Windows
   layout without an authoritative charset file, and one entry was wrong as a result:
   grave was recorded as ``a½``, which is a *TCVN3* byte (0xBD is ẵ there). The entries
   marked below are the ones checked against real VNI documents; the rest still carry
   the original provenance and should be validated the same way before being relied on.

Only well-established sequences are included for now; the table grows as entries
are validated. Unmatched characters pass through unchanged.

The table is five sequences plus ``đ`` against roughly fifty the encoding needs, so a
VNI document comes back mostly unconverted. Measured at 0.246 diacritic accuracy in
``TrizenX/viparse-corpus`` — detection is not the gap, coverage is.
"""

from __future__ import annotations

from viparse.normalize.tables import Charmap, build_charmap

ENCODING_NAME = "vni"

# VNI surface sequence (base letter + mark) → Unicode Vietnamese letter (NFC).
_ENTRIES = [
    # Verified against the VNI documents in TrizenX/viparse-corpus: `aø` occurs 211
    # times (thaønh, haønh, ngaønh, baøn, Caø Mau) and `a½` not once.
    ("aø", "à"),  # a + grave
    ("aù", "á"),  # a + acute
    ("aû", "ả"),  # a + hook
    ("aõ", "ã"),  # a + tilde
    ("aï", "ạ"),  # a + dot below
    ("ñ", "đ"),  # d with stroke
]

VNI: Charmap = build_charmap(ENCODING_NAME, _ENTRIES)
