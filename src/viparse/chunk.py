"""RAG chunking: split a normalized document into retrieval-sized pieces (SPEC-4 E4.2).

Chunking works on the **block structure** (headings / paragraphs / table rows), not the
flat text, so it can:

- keep every chunk within a single section — any section change (a heading, or an empty
  heading that merely resets the section) starts a new chunk, so a chunk's ``section``
  metadata is unambiguous (it never straddles a section boundary);
- **never split a table row** — each row is an atomic unit, and a large table is split at
  row boundaries, with the table's **header row repeated** at the top of every chunk that
  continues it;
- carry per-chunk metadata (``section`` and inherited ``page`` / ``sheet``) plus the
  chunk's ordinal :attr:`~viparse.model.Chunk.index` for downstream provenance.

Token counts are **approximate and tiktoken-free** (whitespace-delimited words), which is
enough to bound chunk size without pinning to any one model's tokenizer. A single block
larger than the target is emitted whole (sub-splitting long paragraphs is a future
refinement); table rows are always kept intact regardless of size.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from viparse.model import Block, Chunk, Heading, NormalizedDoc, Table, blocks_of


@dataclass(frozen=True, slots=True)
class ChunkOptions:
    """Chunking knobs: target size and overlap, both in approximate tokens (words)."""

    max_tokens: int = 512
    overlap_tokens: int = 64


def estimate_tokens(text: str) -> int:
    """Approximate token count for ``text`` (tiktoken-free: whitespace-delimited words)."""
    return len(text.split())


@dataclass(frozen=True, slots=True)
class _Unit:
    """An atomic chunkable piece — a heading, a paragraph, or a single table row."""

    text: str
    section: str
    is_heading: bool
    #: For a table row that is not itself the header, that table's header row. A chunk
    #: beginning here repeats it, so retrieved rows never arrive without their columns.
    header: str = ""


def chunk_document(document: NormalizedDoc, options: ChunkOptions) -> list[Chunk]:
    """Split ``document`` into overlapping, single-section :class:`~viparse.model.Chunk`s."""
    units = list(_iter_units(blocks_of(document)))
    if not units:
        return []

    chunks: list[Chunk] = []
    start = 0
    count = len(units)
    while True:  # always terminates via the `end >= count` break below (count >= 1 here)
        end = start
        # A chunk opening mid-table will repeat that table's header, so charge it to the
        # budget up front rather than letting the chunk quietly exceed max_tokens.
        tokens = estimate_tokens(units[start].header)
        while end < count:
            if end > start and _crosses_section(units, start, end):
                break  # a new section starts here — never split one across chunks
            unit_tokens = estimate_tokens(units[end].text)
            if end > start and tokens + unit_tokens > options.max_tokens:
                break  # this unit would overflow — leave it for the next chunk
            tokens += unit_tokens
            end += 1
        chunks.append(_make_chunk(units[start:end], len(chunks), document))
        if end >= count:
            break
        # Overlap stays within a section: a section boundary starts the next chunk fresh.
        if _crosses_section(units, start, end):
            start = end
        else:
            start = _next_start(units, start, end, options)
    return chunks


def _crosses_section(units: list[_Unit], start: int, end: int) -> bool:
    """Whether ``units[end]`` opens a new section relative to the chunk started at ``start``.

    True at an explicit heading unit *and* when the section label merely changes (an
    empty-text heading resets the section without emitting a unit of its own), so a chunk
    can never straddle a section boundary regardless of how it was introduced.
    """
    return units[end].is_heading or units[end].section != units[start].section


def _iter_units(blocks: list[Block]) -> Iterator[_Unit]:
    """Flatten blocks into atomic units, tracking the section each unit belongs to."""
    section = ""
    for block in blocks:
        if isinstance(block, Heading):
            section = block.text
            if block.text:
                yield _Unit(text=block.text, section=section, is_heading=True)
        elif isinstance(block, Table):
            # The first non-blank row is the header — the same assumption the Markdown
            # renderer already makes when it writes the `| --- |` rule after row one.
            header = ""
            for row in block.rows:
                if not any(cell.strip() for cell in row):  # skip an all-blank row
                    continue
                text = "\t".join(row)
                yield _Unit(text=text, section=section, is_heading=False, header=header)
                if not header:
                    header = text
        elif block.text:  # Paragraph
            yield _Unit(text=block.text, section=section, is_heading=False)


def _continued_table_header(group: list[_Unit]) -> str:
    """The header row to repeat above ``group``, or ``""`` if none is needed.

    A chunk that begins part-way through a table would otherwise open on bare data —
    ``Tăng trưởng GDP  5,66%  6,42%`` with nothing saying which column is which. Retrieval
    surfaces that chunk on its own, so whatever reads it has to guess.

    Nothing is repeated when the header is already in the group, which happens whenever
    the overlap reached back far enough.
    """
    header = group[0].header
    if not header or any(unit.text == header for unit in group):
        return ""
    return header


def _make_chunk(group: list[_Unit], index: int, document: NormalizedDoc) -> Chunk:
    metadata: dict[str, object] = {
        "section": group[0].section,  # every unit in the group shares one section
        "page": document.page,
        "sheet": document.sheet,
    }
    lines = [unit.text for unit in group]
    header = _continued_table_header(group)
    if header:
        lines.insert(0, header)
        metadata["table_header_repeated"] = True
    return Chunk(text="\n".join(lines), metadata=metadata, index=index)


def _next_start(units: list[_Unit], start: int, end: int, options: ChunkOptions) -> int:
    """Where the next chunk begins: back up from ``end`` to repeat ~``overlap_tokens``.

    Never returns ``<= start``, so the scan always makes progress (an overlap larger than
    the chunk simply repeats everything but the first unit). ``units[start:end]`` share one
    section, so this overlap never crosses a heading boundary.
    """
    cursor = end
    tokens = 0
    while cursor > start + 1 and tokens < options.overlap_tokens:
        cursor -= 1
        tokens += estimate_tokens(units[cursor].text)
    return cursor
