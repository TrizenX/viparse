"""Registry of the available legacy-encoding conversion tables.

New encodings register their :class:`~viparse.normalize.tables.Charmap` here so
the detector and normalizer can look them up by name.
"""

from __future__ import annotations

import unicodedata

from viparse.normalize.tables import Charmap
from viparse.normalize.tcvn3 import TCVN3
from viparse.normalize.viscii import VISCII
from viparse.normalize.vni import VNI
from viparse.normalize.vps import VPS


def _register(*charmaps: Charmap) -> dict[str, Charmap]:
    """Index charmaps by name, raising if two share a name (a copy-paste slip)."""
    registry: dict[str, Charmap] = {}
    for charmap in charmaps:
        if charmap.name in registry:
            raise ValueError(f"duplicate encoding name {charmap.name!r}")
        registry[charmap.name] = charmap
    return registry


CHARMAPS: dict[str, Charmap] = _register(TCVN3, VNI, VISCII, VPS)

# Candidates for content-frequency auto-detection (SPEC-3 E3.2). VPS is deliberately
# excluded: it keys the same Latin-1 surface bytes as VISCII to *different* Vietnamese
# letters, so offering it as a trial candidate lets a genuine VISCII document be mis-scored
# as VPS and silently corrupted — the moat's cardinal sin. Its uppercase letters also live
# in C0 control bytes that cleanup strips before detection, making auto-detection of VPS
# unreliable regardless. VPS therefore converts only via an explicit ``encoding="vps"``
# override, never by auto-detection.
AUTO_DETECT_CHARMAPS: dict[str, Charmap] = {
    name: charmap for name, charmap in CHARMAPS.items() if name != VPS.name
}


def control_chars_in(charmaps: dict[str, Charmap]) -> frozenset[str]:
    """Characters these charmaps read as letters but Unicode classes as control codes.

    VISCII puts **38 of its 103 letters** in the C0 and C1 ranges — 6 in C0 (Ẳ Ẵ Ẫ Ỷ Ỹ Ỵ)
    and 32 in C1 (Ạ Ộ Ế Ề Ệ Ị Ọ Ủ Ụ among them). VPS is worse at 44 of 112. Stripping
    control characters before content detection therefore deletes over a third of the
    evidence detection needs, and VISCII scores near zero on its own text — which is why
    a canonical VISCII header returned ``encoding_detected=None`` before VIP-93.

    Computed from the tables rather than listed, so a table that gains an entry in the
    control ranges is covered without anyone remembering to update a constant.
    """
    return frozenset(
        ch
        for charmap in charmaps.values()
        for source, _ in charmap.pairs
        for ch in source
        if unicodedata.category(ch) in ("Cc", "Cf")
    )


def get_charmap(name: str) -> Charmap | None:
    """Return the registered charmap for ``name``, or ``None`` if unknown."""
    return CHARMAPS.get(name)
