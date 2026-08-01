"""VNI (VNI-Windows / ``VNI-Times`` fonts) → Unicode conversion table.

VNI is a **composite** encoding: a toned Vietnamese vowel is stored as a base
Latin letter followed by one or two mark characters from the upper byte range.
When extracted, those surface as a base letter plus the matching Latin-1/CP1252
characters, so the conversion sequences here are multi-character (e.g. ``a`` +
mark → ``á``). The framework matches longest sequences first, so ``aù`` is
converted before a bare ``a`` is ever considered.

Four letters are written as a single character rather than base + mark, because
Latin-1 has no bare i-family letter to hang a mark on: ``ñ`` ``ò`` ``æ`` ``ó``
are đ ị ỉ ĩ. This section is easy to get backwards — ``ì`` and ``í`` are already
the letters they look like (``cheát vì`` is chết vì, ``Chi phí`` is chi phí).

Provenance
----------
Derived against the VNI documents in `viparse-corpus
<https://github.com/TrizenX/viparse-corpus>`_ — 53,715 characters over four real
Vietnamese administrative documents — not transcribed from a layout chart. Each
entry below carries either its **occurrence count** in that corpus or the marker
``derived``.

- **104 entries are observed directly**, most of them many times over: ``ö`` → ư
  927 times, ``ñ`` → đ 788, ``aø`` → à 628.
- **26 are derived**, and only from two rules that are themselves observed
  dozens of times: uppercase text pairs an uppercase base with an uppercase
  modifier (42 uppercase entries observed, ``AØ`` → À 27 times, ``OÄ`` → Ộ 18),
  and a bare vowel takes a tone mark directly (46 observed). They are the
  specific combinations that happen not to occur in 53k characters, not new
  rules.

Known gaps
----------
**ẳ ẵ Ẳ Ẵ are deliberately absent.** No VNI document collected so far contains
any of them, and every one of the 25 distinct modifier characters that *does*
follow a base vowel in that corpus is already mapped here — so these are
unobserved rather than overlooked. Filling them by symmetry with the ắ/ằ/ặ row
is exactly how the old ``a½`` entry came to be written: ``0xBD`` is a TCVN3 byte
(ẵ there), it appears in no VNI document, and because it occupied the grave slot
the correct ``aø`` was missing and à was never converted at all (VIP-89).

Unmatched characters pass through unchanged, so a document containing ẳ returns
it unconverted rather than silently wrong.
"""

from __future__ import annotations

from viparse.normalize.tables import Charmap, build_charmap

ENCODING_NAME = "vni"

# VNI surface sequence (base letter + mark) → Unicode Vietnamese letter (NFC).
# Counts are occurrences in viparse-corpus; `derived` is explained in the module
# docstring. Generated from the corpus rather than typed, because a table typed by
# hand is how the TCVN3 sibling got four entries wrong on its first pass.
_ENTRIES = [
    # --- đ / Đ -----------------------------------------------------
    ("ñ", "đ"),  # ×788
    ("Ñ", "Đ"),  # ×241
    # --- a ă â -----------------------------------------------------
    ("aø", "à"),  # ×628
    ("aù", "á"),  # ×594
    ("aï", "ạ"),  # ×283
    ("aû", "ả"),  # ×231
    ("aá", "ấ"),  # ×174
    ("aä", "ậ"),  # ×123
    ("aê", "ă"),  # ×122
    ("aâ", "â"),  # ×77
    ("aõ", "ã"),  # ×45
    ("aà", "ầ"),  # ×43
    ("aå", "ẩ"),  # ×35
    ("aé", "ắ"),  # ×29
    ("aë", "ặ"),  # ×29
    ("AØ", "À"),  # ×27
    ("aè", "ằ"),  # ×16
    ("AÙ", "Á"),  # ×13
    ("AÂ", "Â"),  # ×11
    ("AÛ", "Ả"),  # ×11
    ("aã", "ẫ"),  # ×7
    ("AÕ", "Ã"),  # ×5
    ("AÏ", "Ạ"),  # ×4
    ("AÊ", "Ă"),  # ×2
    ("AÁ", "Ấ"),  # ×2
    ("AÅ", "Ẩ"),  # ×2
    ("AÄ", "Ậ"),  # ×2
    ("AÀ", "Ầ"),  # ×1
    ("AÃ", "Ẫ"),  # derived
    ("AÉ", "Ắ"),  # derived
    ("AÈ", "Ằ"),  # derived
    ("AË", "Ặ"),  # derived
    # --- e ê -------------------------------------------------------
    ("eä", "ệ"),  # ×466
    ("eá", "ế"),  # ×272
    ("eà", "ề"),  # ×243
    ("eâ", "ê"),  # ×239
    ("eå", "ể"),  # ×175
    ("eù", "é"),  # ×33
    ("EÄ", "Ệ"),  # ×16
    ("eû", "ẻ"),  # ×13
    ("eõ", "ẽ"),  # ×11
    ("EÁ", "Ế"),  # ×7
    ("EÀ", "Ề"),  # ×7
    ("eã", "ễ"),  # ×7
    ("EÂ", "Ê"),  # ×4
    ("eø", "è"),  # ×4
    ("eï", "ẹ"),  # ×1
    ("EÅ", "Ể"),  # ×1
    ("EØ", "È"),  # derived
    ("EÙ", "É"),  # derived
    ("EÏ", "Ẹ"),  # derived
    ("EÛ", "Ẻ"),  # derived
    ("EÕ", "Ẽ"),  # derived
    ("EÃ", "Ễ"),  # derived
    # --- i ---------------------------------------------------------
    ("ò", "ị"),  # ×291
    ("æ", "ỉ"),  # ×146
    ("Ò", "Ị"),  # ×17
    ("Æ", "Ỉ"),  # ×9
    ("Ó", "Ĩ"),  # ×5
    ("ó", "ĩ"),  # ×5
    ("IØ", "Ì"),  # derived
    ("IÙ", "Í"),  # derived
    ("iø", "ì"),  # derived
    ("iù", "í"),  # derived
    # --- o ô ơ -----------------------------------------------------
    ("ô", "ơ"),  # ×786
    ("oä", "ộ"),  # ×288
    ("oâ", "ô"),  # ×267
    ("oá", "ố"),  # ×205
    ("ôï", "ợ"),  # ×199
    ("où", "ó"),  # ×138
    ("ôø", "ờ"),  # ×137
    ("ôû", "ở"),  # ×125
    ("ôù", "ớ"),  # ×112
    ("oø", "ò"),  # ×70
    ("oå", "ổ"),  # ×66
    ("oà", "ồ"),  # ×50
    ("oï", "ọ"),  # ×26
    ("OÄ", "Ộ"),  # ×18
    ("oã", "ỗ"),  # ×14
    ("Ô", "Ơ"),  # ×12
    ("oû", "ỏ"),  # ×11
    ("oõ", "õ"),  # ×9
    ("OÂ", "Ô"),  # ×7
    ("ôõ", "ỡ"),  # ×6
    ("ÔÛ", "Ở"),  # ×5
    ("OÅ", "Ổ"),  # ×3
    ("OÁ", "Ố"),  # ×2
    ("OØ", "Ò"),  # ×1
    ("OÙ", "Ó"),  # ×1
    ("OÀ", "Ồ"),  # ×1
    ("ÔÙ", "Ớ"),  # ×1
    ("ÔØ", "Ờ"),  # ×1
    ("OÕ", "Õ"),  # derived
    ("OÏ", "Ọ"),  # derived
    ("OÛ", "Ỏ"),  # derived
    ("OÃ", "Ỗ"),  # derived
    ("ÔÕ", "Ỡ"),  # derived
    ("ÔÏ", "Ợ"),  # derived
    # --- u ư -------------------------------------------------------
    ("ö", "ư"),  # ×927
    ("uû", "ủ"),  # ×221
    ("öï", "ự"),  # ×149
    ("uï", "ụ"),  # ×148
    ("öù", "ứ"),  # ×123
    ("öû", "ử"),  # ×85
    ("öø", "ừ"),  # ×55
    ("uù", "ú"),  # ×38
    ("öõ", "ữ"),  # ×37
    ("uø", "ù"),  # ×24
    ("Ö", "Ư"),  # ×18
    ("UÛ", "Ủ"),  # ×14
    ("uõ", "ũ"),  # ×11
    ("ÖÙ", "Ứ"),  # ×6
    ("UÕ", "Ũ"),  # ×5
    ("UÏ", "Ụ"),  # ×5
    ("ÖÛ", "Ử"),  # ×3
    ("ÖÕ", "Ữ"),  # ×1
    ("ÖÏ", "Ự"),  # ×1
    ("UØ", "Ù"),  # derived
    ("UÙ", "Ú"),  # derived
    ("ÖØ", "Ừ"),  # derived
    # --- y ---------------------------------------------------------
    ("yù", "ý"),  # ×89
    ("yõ", "ỹ"),  # ×20
    ("yû", "ỷ"),  # ×14
    ("yø", "ỳ"),  # ×10
    ("YÙ", "Ý"),  # ×6
    ("YÛ", "Ỷ"),  # ×3
    ("YØ", "Ỳ"),  # ×1
    ("YÏ", "Ỵ"),  # derived
    ("yï", "ỵ"),  # derived
    ("YÕ", "Ỹ"),  # derived
]

VNI: Charmap = build_charmap(ENCODING_NAME, _ENTRIES)
