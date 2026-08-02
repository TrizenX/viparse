"""Shared framework for legacy Vietnamese encoding → Unicode conversion.

A legacy encoding (TCVN3, VNI, VISCII) is described by a :class:`Charmap`: an
ordered set of *(legacy sequence → Unicode replacement)* pairs. When a document
is authored in a legacy font, extraction yields the **font's** code points as
ordinary Unicode characters — e.g. the TCVN3 byte ``0xB5`` surfaces as U+00B5
``µ``. Converting means replacing each legacy sequence with the correct
Vietnamese character, then normalizing to NFC.

Matching is greedy and longest-first, so a multi-character legacy form (VNI
encodes a toned vowel as *base + mark*) is matched before any shorter sequence
that is its prefix. Conversion is a single left-to-right scan, so a replacement's
output can never be re-matched as another sequence's input.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from functools import cache

from viparse.options import NormalizeForm


@dataclass(frozen=True)
class Charmap:
    """An immutable legacy-encoding → Unicode conversion table.

    ``pairs`` are ``(legacy_sequence, unicode_replacement)`` tuples, pre-sorted
    longest sequence first. Build one with :func:`build_charmap` rather than
    constructing it directly, so the ordering and validation invariants hold.
    """

    name: str
    pairs: tuple[tuple[str, str], ...]


def build_charmap(name: str, entries: Iterable[tuple[str, str]]) -> Charmap:
    """Build a :class:`Charmap` from ``(legacy_sequence, unicode)`` pairs.

    A list of pairs (rather than a dict literal) lets this function catch a
    duplicated legacy sequence — a dict would silently collapse it. Raises
    ``ValueError`` on an empty source, an empty replacement (which would delete
    the character), or a duplicate legacy sequence (an ambiguous table).
    """
    seen: set[str] = set()
    pairs: list[tuple[str, str]] = []
    for legacy_seq, replacement in entries:
        if not legacy_seq:
            raise ValueError(f"{name}: legacy sequence must not be empty")
        if not replacement:
            raise ValueError(f"{name}: replacement for {legacy_seq!r} must not be empty")
        if legacy_seq in seen:
            raise ValueError(f"{name}: duplicate legacy sequence {legacy_seq!r}")
        seen.add(legacy_seq)
        pairs.append((legacy_seq, replacement))
    pairs.sort(key=lambda pair: len(pair[0]), reverse=True)
    return Charmap(name=name, pairs=tuple(pairs))


@cache
def _first_char_index(charmap: Charmap) -> dict[str, tuple[tuple[str, str], ...]]:
    """Group a charmap's pairs by their first character (cached per charmap)."""
    grouped: dict[str, list[tuple[str, str]]] = {}
    for legacy_seq, replacement in charmap.pairs:
        grouped.setdefault(legacy_seq[0], []).append((legacy_seq, replacement))
    return {first: tuple(items) for first, items in grouped.items()}


# Codepoints a PDF text layer puts out in place of a legacy byte.
#
# A PDF stores glyph codes and the extractor resolves them through the font's encoding.
# For `.VnTime` that turns TCVN3's `0xAD` — the soft-hyphen slot, which is the letter ư —
# into U+2212 MINUS SIGN, and `0xB7` (ã) into U+2219 BULLET OPERATOR.
#
# This is the third mechanism by which the same letter goes missing. A legacy `.doc`
# loses ư through `<w:softHyphen/>` (VIP-87); a PDF loses it here. Measured over the five
# legacy PDFs in viparse-corpus: 129 occurrences of U+2212, every one of them a letter —
# `nhµ n−íc` is nhà nước, `Thñ t−íng` is Thủ tướng, `Th«ng t−` is Thông tư.
_GLYPH_SUBSTITUTIONS = {"\u2212": "\xad", "\u2219": "\xb7"}


def _restore_substituted_glyphs(text: str) -> str:
    """Undo the PDF glyph substitutions, but only where the result is a letter.

    Adjacency decides, and it has to: a minus sign between digits is a minus sign, and a
    statistics table full of them is exactly the kind of document this runs on. Across
    the corpus PDFs no substituted codepoint sits between digits and none of the 129
    genuine ones lacks a letter neighbour, so the rule separates them cleanly.

    Only reached once a legacy encoding has been established — `convert` is not called
    otherwise — so text that is already Unicode never passes through here.
    """
    if not any(char in text for char in _GLYPH_SUBSTITUTIONS):
        return text
    out = list(text)
    for position, char in enumerate(text):
        replacement = _GLYPH_SUBSTITUTIONS.get(char)
        if replacement is None:
            continue
        before = text[position - 1] if position else ""
        after = text[position + 1] if position + 1 < len(text) else ""
        if before.isalpha() or after.isalpha():
            out[position] = replacement
    return "".join(out)


def convert(text: str, charmap: Charmap, normalize_form: NormalizeForm = "NFC") -> str:
    """Convert legacy-encoded ``text`` to Unicode using ``charmap``, then normalize.

    A single left-to-right scan replaces each matched legacy sequence (longest
    first) with its Unicode form; unmatched characters pass through unchanged.
    """
    text = _restore_substituted_glyphs(text)
    index = _first_char_index(charmap)
    out: list[str] = []
    position = 0
    length = len(text)
    while position < length:
        char = text[position]
        for legacy_seq, replacement in index.get(char, ()):
            if text.startswith(legacy_seq, position):
                out.append(replacement)
                position += len(legacy_seq)
                break
        else:
            out.append(char)
            position += 1
    return unicodedata.normalize(normalize_form, "".join(out))
