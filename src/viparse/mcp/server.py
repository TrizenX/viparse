"""MCP server exposing viparse to agents.

A thin wrapper over the public API — no parsing logic lives here, and the safety limits,
path handling and layered options are whatever :func:`viparse.load` already enforces.

Why the tool descriptions read the way they do
----------------------------------------------
An agent never thinks *"I should use viparse"*. It encounters ``B¸o c¸o tµi chÝnh`` in a
file it just read and needs something that knows what that is. So the descriptions are
written around the **symptom** — the mojibake itself, the font names, the encoding names
— rather than around the product's own vocabulary. A description that says "parses
Vietnamese documents" is invisible to an agent that does not yet know the word
"viparse"; one that contains ``tµi chÝnh`` is found by pattern.

That is also why the repair tool takes a **string** and not only a path. Most of the time
the agent already has the broken text in context, pasted or returned by some other tool,
and there is no file to point at.
"""

from __future__ import annotations

from typing import Any

from viparse import __version__

_INSTRUCTIONS = """\
Tools for Vietnamese text that came out of a document wrong.

Reach for these when you see Vietnamese that looks like `B¸o c¸o tµi chÝnh`, `Coäng hoøa
xaõ hoäi`, `QuyÕt ®Þnh`, or any text where the diacritics have turned into unrelated
Latin-1 characters. That is not corruption and it is not lost — it is a pre-Unicode
Vietnamese encoding (TCVN3, VNI, VISCII or VPS) being read as if it were Latin-1, and it
converts back exactly.
"""


def build_server() -> Any:
    """Construct the MCP server. Imported lazily so ``mcp`` stays an optional extra."""
    from mcp.server.mcpserver import MCPServer

    server = MCPServer(
        name="viparse",
        title="Vietnamese legacy-encoding document parser",
        instructions=_INSTRUCTIONS,
        website_url="https://viparse.trizenx.com",
    )

    @server.tool(
        name="repair_garbled_vietnamese",
        title="Repair garbled Vietnamese text",
        description=(
            "Repair Vietnamese text whose diacritics have turned into unrelated "
            "characters — `B¸o c¸o tµi chÝnh` should read `Báo cáo tài chính`, `Coäng "
            "hoøa xaõ hoäi` should read `Cộng hòa xã hội`, `QuyÕt ®Þnh` should read "
            "`Quyết định`.\n\n"
            "This is not corruption and nothing has been lost. The text is in a "
            "pre-Unicode Vietnamese encoding — TCVN3, VNI, VISCII or VPS — being read as "
            "Latin-1, and it converts back exactly. Word documents from Vietnamese "
            "government and university sources before roughly 2010 are usually TCVN3 "
            "(fonts named `.VnTime`, `.VnTimeH`) or VNI (`VNI-Times`).\n\n"
            "Pass the text you already have; you do not need the original file. Text "
            "that is already Unicode is returned unchanged."
        ),
    )
    def repair_garbled_vietnamese(text: str, encoding: str = "auto") -> str:
        """:param encoding: ``tcvn3``/``vni``/``viscii``/``vps``, or ``auto`` to detect."""
        return _repair(text, encoding)

    @server.tool(
        name="identify_vietnamese_encoding",
        title="Identify which legacy Vietnamese encoding text is in",
        description=(
            "Say which pre-Unicode Vietnamese encoding a piece of garbled text is in — "
            "TCVN3, VNI, VISCII or VPS — without changing it. Use this to check before "
            "converting a large batch, or to explain what a user is looking at.\n\n"
            "Returns the detected encoding and a short preview of how the text reads once "
            "converted, so the answer can be judged rather than trusted."
        ),
    )
    def identify_vietnamese_encoding(text: str) -> dict[str, Any]:
        repaired = _repair(text, "auto")
        return {
            "encoding": _detect(text),
            "unchanged": repaired == text,
            "preview": repaired[:200],
            "note": (
                "`unchanged: true` means either the text is already Unicode, or it is in "
                "an encoding with no distinctive signal in this sample. Try a longer "
                "sample before concluding it is Unicode."
            ),
        }

    @server.tool(
        name="read_vietnamese_document",
        title="Read a document that comes out as garbled Vietnamese",
        description=(
            "Read a `.doc`, `.docx`, `.pdf`, `.rtf` or `.xlsx` whose Vietnamese text "
            "comes out garbled — `B¸o c¸o tµi chÝnh` instead of `Báo cáo tài chính` — "
            "and return it as correct Unicode.\n\n"
            "Use this instead of a generic document reader when the file is Vietnamese "
            "and old, or when a generic reader has already returned text like that. "
            "Legacy `.doc` needs LibreOffice installed.\n\n"
            'Returns markdown by default; pass `output="text"` for plain text.'
        ),
    )
    def read_vietnamese_document(
        path: str, output: str = "markdown", encoding: str | None = None
    ) -> str:
        from viparse import load

        options: dict[str, Any] = {"output": output}
        if encoding is not None:
            options["encoding"] = encoding
        return "\n\n".join(document.text for document in load(path, **options))

    @server.tool(
        name="viparse_version",
        title="viparse version",
        description="The installed viparse version, for bug reports.",
    )
    def viparse_version() -> str:
        return __version__

    return server


def _repair(text: str, encoding: str) -> str:
    from viparse import fix

    return fix(text, encoding=encoding)


def _detect(text: str) -> str | None:
    from viparse import detect_text_encoding

    return detect_text_encoding(text)


def main() -> None:
    """Entry point for ``viparse-mcp`` and ``python -m viparse.mcp``."""
    build_server().run()
