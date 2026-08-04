"""Execute the conversions the READMEs claim, instead of trusting them.

``tests/test_skill.py`` already applies this to the agent skill, for a reason that
applies here too: a document whose examples do not run is worse than no document,
because a reader follows it, gets a different answer, and has no reason to doubt the
instruction.

It matters more for ``README.vi.md``. The English README is the one every contributor
reads, so a wrong example there gets noticed; the Vietnamese one can drift for a long
time without anyone checking it against the code — which is exactly the situation a
test is for.

An example is any line calling into ``viparse`` whose expected result is written as a
quoted literal in a comment, either inline or on the line below:

    viparse.fix("Coäng hoøa")        # 'Cộng hòa'

    viparse.fix("B¸o c¸o")
    # → 'Báo cáo'

A comment carrying prose rather than a literal is documentation, not a claim, and is
skipped — ``# ép bảng mã, bỏ qua bước dò`` says what the line is for, not what it
returns.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

import viparse

READMES = [Path(__file__).resolve().parent.parent / name for name in ("README.md", "README.vi.md")]

# A call into the package, then a comment whose first token is a string literal or None.
#
# The argument match is non-greedy, and the line must end after an optional comment.
# Greedy here silently swallowed the comment on
#     viparse.detect_text_encoding("B¸o c¸o")   # 'tcvn3'  (hoặc None nếu không tìm ra)
# by closing on the final ")" in the prose, which dropped the example rather than
# failing on it — the count assertion below is what caught that.
_CALL = re.compile(r"^\s*(viparse\.[A-Za-z_]\w*\(.*?\))\s*(?:#\s*(?:→\s*)?(.*))?$")
_RESULT = re.compile(r"^('[^']*'|\"[^\"]*\"|None)")


def _examples(path: Path) -> list[tuple[str, object]]:
    """``(expression, expected)`` for every claim in one file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    found: list[tuple[str, object]] = []
    for index, line in enumerate(lines):
        call = _CALL.match(line)
        if not call:
            continue
        expression, comment = call.group(1), call.group(2) or ""
        if not _RESULT.match(comment.strip()):
            # The result may be on the following line instead of inline.
            following = lines[index + 1].strip() if index + 1 < len(lines) else ""
            comment = (
                following.lstrip("#").lstrip("→ ").strip() if following.startswith("#") else ""
            )
        result = _RESULT.match(comment.strip())
        if result:
            found.append((expression, ast.literal_eval(result.group(1))))
    return found


ALL = [(path, expression, expected) for path in READMES for expression, expected in _examples(path)]


@pytest.mark.parametrize(
    ("path", "expression", "expected"),
    ALL,
    ids=[f"{path.name}:{expression}" for path, expression, _ in ALL],
)
def test_readme_example(path: Path, expression: str, expected: object) -> None:
    assert eval(expression, {"viparse": viparse}) == expected  # noqa: S307 - our own docs


def test_vietnamese_readme_has_examples_to_run() -> None:
    """Guard the guard.

    Every check above is generated from the file, so a parser that stops matching —
    after a reformat, or a rename — produces zero cases and a green suite. Silence is
    the failure mode of a data-driven test, so the count is asserted directly.
    """
    vi = next(p for p in READMES if p.name == "README.vi.md")
    found = _examples(vi)
    assert len(found) >= 3, "README.vi.md carried three runnable examples when this was written"
    assert any("Cộng hòa xã hội chủ nghĩa" == expected for _, expected in found)
