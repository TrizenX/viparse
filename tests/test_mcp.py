"""The MCP server (VIP-100).

The server is a thin wrapper, so these tests are about the wrapper's contract rather
than about parsing: that the tools are registered, that they carry the *symptom* in
their descriptions, and that the two string tools behave on text with no file behind it.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

pytest.importorskip("mcp")

from viparse.mcp import build_server  # noqa: E402

_GARBLED = {
    "B¸o c¸o tµi chÝnh": "Báo cáo tài chính",
    "Coäng hoøa xaõ hoäi chuû nghóa Vieät Nam": "Cộng hòa xã hội chủ nghĩa Việt Nam",
}


def _call(name: str, arguments: dict[str, Any]) -> str:
    result = asyncio.run(build_server().call_tool(name, arguments))
    content = result.content if hasattr(result, "content") else result[0]
    return "".join(part.text for part in content)


def _tools() -> list[Any]:
    return asyncio.run(build_server().list_tools())


def test_every_tool_is_registered() -> None:
    names = {tool.name for tool in _tools()}
    assert names == {
        "repair_garbled_vietnamese",
        "identify_vietnamese_encoding",
        "read_vietnamese_document",
        "viparse_version",
    }


@pytest.mark.parametrize(("garbled", "expected"), list(_GARBLED.items()))
def test_repair_converts_text_with_no_file_behind_it(garbled: str, expected: str) -> None:
    """The common case is text already in the agent's context, not a path.

    An agent that has been handed `B¸o c¸o tµi chÝnh` by some other tool has nothing to
    point `read_vietnamese_document` at.
    """
    assert _call("repair_garbled_vietnamese", {"text": garbled}) == expected


def test_repair_leaves_unicode_alone() -> None:
    """The moat's cardinal rule, at the tool boundary: never damage correct text."""
    text = "Đã là Unicode rồi, không cần sửa gì"
    assert _call("repair_garbled_vietnamese", {"text": text}) == text


def test_identify_returns_every_field_its_description_promises() -> None:
    """A description that promises a field the tool omits is a bug an agent hits at runtime.

    This one promised a confidence and did not return it.
    """
    payload = json.loads(
        _call("identify_vietnamese_encoding", {"text": "Coäng hoøa xaõ hoäi chuû nghóa"})
    )
    assert set(payload) >= {"encoding", "confidence", "preview"}


def test_identify_names_the_encoding_and_shows_its_work() -> None:
    """A verdict an agent cannot check is a verdict it has to trust blindly."""
    payload = json.loads(
        _call(
            "identify_vietnamese_encoding",
            {"text": "Coäng hoøa xaõ hoäi chuû nghóa Vieät Nam"},
        )
    )
    assert payload["encoding"] == "vni"
    assert 0 < payload["confidence"] <= 1
    assert payload["unchanged"] is False
    assert "Cộng hòa xã hội" in payload["preview"]


# The symptoms an agent actually sees. A description written in the product's own
# vocabulary — "parses Vietnamese documents" — is invisible to an agent that does not yet
# know the word "viparse"; one containing `tµi chÝnh` is found by pattern matching on the
# broken text itself. This test exists because that property is easy to lose in an edit
# that is only trying to tighten the wording.
_SYMPTOMS = ["B¸o c¸o tµi chÝnh", "TCVN3", "VNI", "Vietnamese"]


@pytest.mark.parametrize("symptom", _SYMPTOMS)
def test_descriptions_carry_the_symptom_not_just_the_product_name(symptom: str) -> None:
    descriptions = " ".join(tool.description or "" for tool in _tools())
    assert symptom in descriptions


def test_no_tool_leads_with_the_product_name() -> None:
    """`viparse_version` may name it; a discovery tool that does is one nobody finds."""
    for tool in _tools():
        if tool.name == "viparse_version":
            continue
        assert not (tool.description or "").lower().startswith("viparse")
