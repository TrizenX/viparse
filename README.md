# viparse

> Vietnamese-first document loader for RAG.

[![PyPI](https://img.shields.io/pypi/v/viparse)](https://pypi.org/project/viparse/)
[![Python](https://img.shields.io/pypi/pyversions/viparse)](https://pypi.org/project/viparse/)
[![License](https://img.shields.io/pypi/l/viparse)](LICENSE)

**Website:** [viparse.trizenx.com](https://viparse.trizenx.com)

One command turns any Vietnamese document — including legacy **TCVN3/VNI/VISCII** fonts, scanned
PDFs, and old `.doc`/`.xls` files — into clean Unicode **NFC** Markdown/JSON, ready to push into a
vector DB.

## Why

Generic loaders *parse the file* but often emit **garbled diacritics** (legacy fonts) or **wrong
Unicode normalization**. `viparse` handles exactly that Vietnamese layer: detect & convert legacy
encodings to Unicode, enforce NFC, and offer diacritic-aware OCR.

**Backbone principle:** never hand-write a parser. Wrap well-maintained engines behind thin
adapters; if an engine gets a CVE or is abandoned, swap the adapter without touching the rest.
Heavy dependencies are lazy-imported via extras (`viparse[ocr]`, `viparse[office]`).

## Where viparse fits

viparse is **not** a general-purpose document loader and does not try to replace one. Tools like
**Unstructured**, **LlamaParse** and **docling** cover a far wider matrix of formats, layout
analysis and table reconstruction; viparse covers one layer they are not built around — the
Vietnamese text layer.

The concrete gap: a document authored in a pre-Unicode Vietnamese font stores *Latin* bytes that
only render as Vietnamese when the original `.VnTime`/`VNI` font is applied. A faithful extractor
returns those bytes faithfully — and faithfully wrong:

```
extracted   B¸o c¸o tµi chÝnh quý II n¨m 2026
correct     Báo cáo tài chính quý II năm 2026
```

Embeddings built on the first string retrieve nothing. viparse detects the legacy encoding, maps
it to real Vietnamese letters and enforces NFC, so the text that reaches your vector DB is the
text a human would read.

Use it as the loader for a Vietnamese-heavy corpus, or as a normalization pass over text another
loader produced. A published head-to-head benchmark on diacritic accuracy is planned for v0.2 —
until it exists, this section deliberately makes no accuracy claims against those tools.

## Status

Released and published to [PyPI](https://pypi.org/project/viparse/) — the version badge above
tracks the current release. [`docs/specs/`](docs/specs/README.md) holds the full spec map
(SPEC-0 … SPEC-8) and [`CHANGELOG.md`](CHANGELOG.md) the release notes.

## Installation

Requires **Python 3.11+**. The core install is pure stdlib — every parser and OCR binary lives
behind an extra:

```bash
pip install viparse                # core — pure stdlib, no parser/OCR binaries
pip install "viparse[office]"      # .docx / .xlsx and legacy .doc / .xls
pip install "viparse[pdf]"         # digital PDFs
pip install "viparse[rtf]"         # RTF
pip install "viparse[ocr]"         # scanned PDFs (needs the Tesseract binary)
pip install "viparse[langchain]"   # LangChain document adapter
pip install "viparse[llamaindex]"  # LlamaIndex document adapter
pip install "viparse[mcp]"         # MCP server, for agents
pip install "viparse[all]"         # every engine and adapter
```

`mcp` is deliberately **not** in `all`: `all` is about parsing capability, and installing
every format handler should not start pulling in a server runtime.

Run `viparse doctor` to see which engines your installed extras enable.

## Usage

```python
import viparse

docs = viparse.load("tai_lieu_cu.pdf")  # list[Document], already NFC
docs = viparse.load("bang_luong.xlsx", output="markdown", encoding="auto")
```

`load()` takes the knobs that matter per call — `output` (`text` / `markdown` / `json`),
`encoding` (override detection), `ocr`, `normalize` (NFC by default), `max_bytes`, plus optional
`cache` and `chunk` objects. `load_batch()` accepts the same options plus a `workers` count and
yields one `list[Document]` per source, so a large corpus streams instead of materialising at
once.

```python
from viparse import load_batch
from viparse.cache import DiskCache

for docs in load_batch(paths, output="markdown", workers=8, cache=DiskCache(".viparse-cache")):
    index(docs)
```

Chunking runs on the document's block structure rather than flat text, so a chunk never straddles
a section boundary and a table row is never split in half.

```python
from viparse.integrations.langchain import to_langchain_documents
from viparse.integrations.llamaindex import to_llamaindex_documents
```

```bash
viparse ./docs/**/*.pdf -o md
viparse doctor        # list available engines per installed extras
```

## Using it from an agent

```bash
pip install "viparse[mcp]"
viparse-mcp                        # stdio; also `python -m viparse.mcp`
```

Claude Desktop, Claude Code and anything else that speaks MCP:

```json
{ "mcpServers": { "viparse": { "command": "viparse-mcp" } } }
```

Four tools. `repair_garbled_vietnamese` takes a **string**, not a path, because most of
the time the agent already has the broken text in context and there is no file to point
at. `identify_vietnamese_encoding` names the encoding without changing anything, and
returns a preview so its answer can be judged rather than trusted.
`read_vietnamese_document` is `viparse.load` over a path. `viparse_version` is for bug
reports.

### The agent skill

`skills/garbled-vietnamese-text/SKILL.md` is a Claude-style skill covering the same
ground for agents that do not have the MCP server: how to recognise each encoding, how
to convert, and the traps — never convert text that is already Unicode, a font name is
not proof, one document can be two encodings, and detection needs a phrase rather than a
four-character fragment.

Copy it into `.claude/skills/` (or your agent's equivalent) to use it.

`tests/test_skill.py` **executes every conversion the document claims**, reading the
examples out of the Markdown table rather than duplicating them. A skill whose examples
do not run is worse than no skill: an agent follows it, gets a wrong answer, and has no
reason to doubt the instruction.

### If you change the tool descriptions, keep the symptom in them

This is the one thing about `src/viparse/mcp/server.py` that is not obvious.

An agent never thinks *"I should use viparse"* — it has never heard of it. It encounters
`B¸o c¸o tµi chÝnh` in a file it just read and needs something that recognises that. So
the descriptions are written around the **symptom**: the mojibake itself, the font names
(`.VnTime`, `VNI-Times`), the encoding names. A description that says "parses Vietnamese
documents" is invisible to an agent that does not know the product; one containing
`tµi chÝnh` is found by pattern-matching the broken text.

`tests/test_mcp.py` asserts the symptoms are present, because that property is easy to
lose in an edit that is only trying to tighten the wording.

## Architecture

One pipeline, four layers, each behind a Protocol so implementations stay swappable and testable
with fakes:

```
viparse.load("file")
    │
    ├─ route      detect format from magic bytes, pick engines by priority
    ├─ extract    Engine     → RawExtraction   (raw text + encoding/font signals)
    ├─ normalize  Normalizer → NormalizedDoc   (legacy → Unicode, NFC)
    └─ structure  Renderer   → Document        (text / markdown / json, + chunks)
```

`Pipeline` holds an `EngineRegistry`, a `Normalizer` and a `Renderer`, all injected — the
orchestrator itself depends on no parsing library. The registry returns every engine matching a
content type ordered by priority, and that ordered list *is* the fallback chain: the orchestrator
walks it until one engine succeeds.

| Module                  | Role                                                                          |
| ----------------------- | ----------------------------------------------------------------------------- |
| `detect.py`             | Magic-byte format detection (zip/OOXML, `%PDF`, OLE2 for legacy `.doc`)        |
| `registry.py`           | Priority-ordered engine registry and fallback chain                            |
| `engines/`              | Thin adapters — `docx`, `xlsx`, `pdf`, `rtf`, `ocr`, `legacy`                  |
| `normalize/`            | The moat: `detector`, `tcvn3`, `vni`, `viscii`, `vps`, `frequency`, `cleanup`  |
| `structure/renderer.py` | Blocks → `text` / `markdown` (GFM tables) / versioned `json`                   |
| `chunk.py`              | Section-aware, table-row-atomic chunking                                       |
| `safety.py`             | Size ceiling and zip-bomb guard, applied *before* any parser sees a file       |
| `cache.py`              | Opt-in content-hash cache keyed by hash + options + schema version             |
| `pipeline.py`           | The orchestrator, error policy and metrics hooks                               |

### How encoding detection decides

The primary signal is the **font name** the extraction engine carries out of the document: a
`.Vn*` font implies TCVN3, a `VNI*` font implies VNI. That signal is high confidence, so it runs
by default.

A content-frequency heuristic — trial-convert, then score against a Vietnamese character model —
also ships, but is **opt-in**. A character model cannot reliably separate legacy Vietnamese from
other diacritic-heavy Latin text, so running it unconditionally would corrupt documents it has no
business touching. Text already in Unicode passes through untouched either way.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). The workflow is deliberately narrow:

- **One task = one branch = one commit = one PR.** Branch `vip-<id>-<short-slug>`, commit and PR
  title `VIP-<id> <short imperative>`.
- `main` is protected: a PR must pass `quality` on Python 3.11 / 3.12 / 3.13, plus `build` and
  `audit`.
- Keep a PR scoped to its task; unrelated work gets its own task.

Specs live in [`docs/specs/`](docs/specs/README.md) — a change that alters behaviour should say
which SPEC section it implements.

## License

[MIT](LICENSE) © 2026 Đinh Minh Trí (Kayden)
