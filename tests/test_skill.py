"""The agent skill (VIP-101).

A skill whose examples do not run is worse than no skill: an agent follows it, gets a
wrong answer, and has no reason to doubt the instruction. These tests execute every
conversion the document claims, and check the frontmatter still carries the symptom that
makes the skill discoverable at all.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from viparse.model import RawExtraction
from viparse.normalize.normalizer import VietnameseNormalizer
from viparse.options import LoadOptions

_SKILL = Path(__file__).resolve().parent.parent / "skills" / "garbled-vietnamese-text" / "SKILL.md"


def _text() -> str:
    return _SKILL.read_text(encoding="utf-8")


def _frontmatter() -> str:
    match = re.match(r"---\n(.*?)\n---\n", _text(), flags=re.S)
    assert match is not None, "SKILL.md must open with YAML frontmatter"
    return match.group(1)


def _repair(text: str, encoding: str = "auto") -> str:
    raw = RawExtraction(
        source="<text>",
        content_type="text/plain",
        text=text,
        engine="test",
        signals={"fonts": []},
    )
    return VietnameseNormalizer().normalize(raw, LoadOptions(encoding=encoding)).text


def _table_pairs() -> list[tuple[str, str]]:
    """The `| what you see | what it says |` rows, read out of the document itself.

    Parsed rather than duplicated here, so a row edited in the skill is a row this test
    starts checking — the failure mode being guarded against is the two drifting apart.
    """
    rows = re.findall(r"^\| `([^`]+)` \| ([^|]+?) \|$", _text(), flags=re.M)
    assert len(rows) >= 4
    return [(garbled, plain.strip()) for garbled, plain in rows]


@pytest.mark.parametrize(("garbled", "expected"), _table_pairs())
def test_every_example_in_the_table_converts_as_claimed(garbled: str, expected: str) -> None:
    assert _repair(garbled) == expected


def test_the_short_fragment_warning_is_still_true() -> None:
    """The skill tells the reader detection needs a phrase. Hold it to that.

    If a future detector fixes the short case, this fails and the warning should go —
    stale warnings cost trust the same way stale instructions do.
    """
    assert _repair("laäp") != "lập"
    assert _repair("Ñoäc laäp") == "Độc lập"
    assert _repair("laäp", encoding="vni") == "lập"


def test_frontmatter_triggers_on_the_symptom_not_the_product_name() -> None:
    """An agent that has never heard of viparse must still find this.

    The description is matched against what the agent is looking at, so it has to
    contain the broken text itself.
    """
    description = _frontmatter()
    for symptom in ("B¸o c¸o tµi chÝnh", "Coäng hoøa xaõ hoäi", ".VnTime", "VNI-Times"):
        assert symptom in description
    assert "viparse" not in description.lower()


def test_frontmatter_names_the_skill_after_the_problem() -> None:
    assert "name: garbled-vietnamese-text" in _frontmatter()
