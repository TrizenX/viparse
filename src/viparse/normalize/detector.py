"""Legacy-encoding detector.

Chooses which conversion table (if any) applies to extracted text. The primary,
highest-confidence signal is the **font name** the extraction engine attaches
(SPEC-3 T3.2.2): a ``.Vn*`` font implies TCVN3, a ``VNI*`` font implies VNI.

:func:`detect_encoding_by_content` adds a **content-frequency** heuristic (T3.2.1 /
T3.2.3) — trial-convert and score against a Vietnamese character model — for sources
with no font signal. It is deliberately **not** run by default: a character model
cannot reliably tell legacy Vietnamese from other diacritic-heavy Latin text (Spanish
``ñ``, German ``ß``), so applying it automatically would risk corrupting good text —
the moat's cardinal sin. The normalizer invokes it only when the caller opts in with
``encoding="auto"``, thereby asserting the source is legacy Vietnamese.

Per-block detection for mixed-encoding documents (T3.2.4) remains a future refinement;
detection runs on the whole text, which is also more reliable than scoring a short
block in isolation.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from viparse.normalize.frequency import vietnamese_score
from viparse.normalize.tables import Charmap, convert
from viparse.normalize.tcvn3 import ENCODING_NAME as TCVN3_NAME
from viparse.normalize.vni import ENCODING_NAME as VNI_NAME

# Confidence for each detection outcome.
_FONT_CONFIDENCE = 0.95  # a single legacy font family is a strong, direct signal
_MIXED_CONFIDENCE = 0.6  # two different legacy encodings present — per-file conversion is lossy
_UNICODE_CONFIDENCE = 0.9  # fonts present but none legacy → almost certainly Unicode
_ASSUMED_CONFIDENCE = 0.5  # no usable font information → Unicode assumed, not confirmed

# Content detection thresholds. A legacy decode is accepted only when it both beats
# leaving the text unconverted by _CONTENT_MARGIN *and* clearly separates from the
# next-best table by _CONTENT_SEPARATION — otherwise the input is ambiguous (several
# tables yield plausible Vietnamese) and guessing would risk corrupting good text.
_CONTENT_MARGIN = 0.15
_CONTENT_SEPARATION = 0.05

# Two guards that frequency scoring cannot provide, because frequency scoring cannot
# tell Vietnamese from any other diacritic-heavy Latin language. Measured against the
# character model, real TCVN3 gains +0.244 — while Spanish gains +0.253 and German
# +0.288. Both *beat* genuine Vietnamese, so no margin will ever separate them.
#
# What does separate them is what the conversion *produces*. Rates below are measured
# over the 48 hand-transcribed documents in viparse-corpus versus the same text run
# through the winning table:
#
#                        real Vietnamese (worst)   Spanish   French   German
#   words > 7 letters              0.008             0.095    0.222    0.375
#   words with f/j/w/z             0.016             0.036    0.250    0.171
#
# Vietnamese writes each syllable as its own word, so a long word is close to
# non-existent; and the alphabet has no f, j, w or z. Every European language has both
# in quantity. Neither test alone is enough — a Spanish sample that happens to avoid
# f/j/w/z sits under the alien ceiling — so both are applied.
_ALIEN_LETTERS = frozenset("fjwzFJWZ")
_ALIEN_RATE_CEILING = 0.05
_LONG_WORD_LETTERS = 7
_LONG_WORD_RATE_CEILING = 0.04  # 5x the worst real document, under half the nearest false positive
_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
#: ``EncodingDetection.method`` when the text converted well and then read as another
#: language. Distinct from ``"assumed-unicode"``, which means the evidence was thin.
NOT_VIETNAMESE = "content-not-vietnamese"

_CONTENT_BASE_CONFIDENCE = 0.5
_CONTENT_MAX_CONFIDENCE = 0.85  # content evidence never reaches font-signal certainty

# PDF embeds subsetted fonts under a 6-uppercase-letter tag, e.g. "ABCDEF+.VnTime".
_SUBSET_TAG = re.compile(r"^[A-Z]{6}\+")


@dataclass(frozen=True, slots=True)
class EncodingDetection:
    """The detector's verdict for a piece of text.

    ``encoding`` is the charmap name to convert with, or ``None`` when the text is
    taken to be already Unicode. ``confidence`` is in ``[0, 1]``; ``method`` records
    how the verdict was reached; ``font`` is the font that triggered a legacy match.
    """

    encoding: str | None
    confidence: float
    method: str
    font: str | None = None


def _encoding_for_font(font: str) -> str | None:
    """Map a font name to a legacy encoding, or ``None`` if it is not a legacy font."""
    name = _SUBSET_TAG.sub("", font).upper()
    if name.startswith(".VN"):  # .VnTime, .VnArial, .VnTimeH, .vntime, …
        return TCVN3_NAME
    if name.startswith("VNI"):  # VNI-Times, VNI-Helve, vni-times, …
        return VNI_NAME
    return None


def detect_encoding(fonts: Iterable[str | None]) -> EncodingDetection:
    """Detect the legacy encoding of extracted text from its font-name signals.

    A single legacy font family wins with high confidence (mixed documents commonly
    interleave one legacy font with plain Latin runs). When *two different* legacy
    encodings appear, per-file conversion cannot be right for both, so the first is
    chosen but flagged with low confidence (real per-block handling is T3.2.4). With
    usable fonts present but none legacy, the text is Unicode with high confidence;
    with no usable font information, Unicode is assumed.
    """
    detected: dict[str, str] = {}  # encoding -> first font that implied it
    usable = False
    for font in fonts:
        if not font:
            continue
        usable = True
        encoding = _encoding_for_font(font)
        if encoding is not None and encoding not in detected:
            detected[encoding] = font

    if len(detected) == 1:
        encoding, font = next(iter(detected.items()))
        return EncodingDetection(encoding, _FONT_CONFIDENCE, "font-signal", font)
    if len(detected) > 1:
        encoding, font = next(iter(detected.items()))
        return EncodingDetection(encoding, _MIXED_CONFIDENCE, "font-signal-mixed", font)
    if usable:
        return EncodingDetection(None, _UNICODE_CONFIDENCE, "no-legacy-font")
    return EncodingDetection(None, _ASSUMED_CONFIDENCE, "assumed-unicode")


def detect_encoding_by_content(text: str, candidates: Mapping[str, Charmap]) -> EncodingDetection:
    """Detect a legacy encoding from the text itself, for sources with no font signal.

    Each candidate charmap is trial-applied and its output scored against the Vietnamese
    character model; the charmap whose conversion most improves the score over leaving
    the text unconverted wins, provided the gain clears :data:`_CONTENT_MARGIN` (else the
    text is taken to be already Unicode). This breaks ties between tables that both yield
    some Vietnamese letters and catches sparsely-legacy text. Confidence scales with the
    margin but never reaches font-signal certainty (SPEC-3 T3.2.1 / T3.2.3).
    """
    base = vietnamese_score(text)
    converted: dict[str, str] = {
        name: convert(text, charmap) for name, charmap in candidates.items()
    }
    ranked = sorted(
        ((vietnamese_score(output) - base, name) for name, output in converted.items()),
        reverse=True,
    )
    best_gain, best_name = ranked[0]
    runner_up_gain = ranked[1][0] if len(ranked) > 1 else 0.0
    if best_gain < _CONTENT_MARGIN or best_gain - runner_up_gain < _CONTENT_SEPARATION:
        # Not clearly one legacy encoding — leave the text as Unicode rather than risk
        # a wrong conversion (the moat's "never corrupt good text" rule).
        return EncodingDetection(None, _ASSUMED_CONFIDENCE, "assumed-unicode")
    if not _reads_as_vietnamese(converted[best_name]):
        # The conversion scored well and then failed the Vietnamese check. That is a
        # *positive* finding — the input is some other diacritic-heavy Latin language —
        # and it is reported separately from "not enough to tell", because a caller can
        # act on the two differently. A block that declined for want of evidence should
        # take its neighbour's verdict; a block that is actively Spanish should not.
        return EncodingDetection(None, _ASSUMED_CONFIDENCE, NOT_VIETNAMESE)
    confidence = min(_CONTENT_MAX_CONFIDENCE, _CONTENT_BASE_CONFIDENCE + best_gain)
    return EncodingDetection(best_name, confidence, "content-frequency")


def _reads_as_vietnamese(text: str) -> bool:
    """Whether a converted string looks like Vietnamese rather than another language.

    Counted over words, not characters: `Microsoft` in an otherwise Vietnamese document
    should weigh once, not nine times. Single letters are skipped — an initial in a name
    is evidence of nothing.

    Real documents do contain foreign words. The ceilings are set from the worst of the
    48 corpus transcripts — 1.6% alien, 0% long — so ordinary borrowing passes.

    On a short sample the rates are noisy, and the failure that produces is the safe
    one: a fragment with one English word in it may be left unconverted rather than
    wrongly converted. Detection is already unreliable on fragments for the same reason,
    so this adds no new sharp edge; it declines in the direction of leaving text alone.
    """
    words = [word for word in _WORD.findall(text) if len(word) > 1]
    if not words:
        return True
    alien = sum(1 for word in words if _ALIEN_LETTERS & set(word)) / len(words)
    long_words = sum(1 for word in words if len(word) > _LONG_WORD_LETTERS) / len(words)
    return alien <= _ALIEN_RATE_CEILING and long_words <= _LONG_WORD_RATE_CEILING
