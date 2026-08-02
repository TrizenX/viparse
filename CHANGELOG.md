# Changelog

All notable changes to viparse are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.19] — 2026-08-02

### Added

- **PowerPoint: `.pptx` and legacy `.ppt`.** `.pptx` was recognised by format detection
  and then failed with `EngineUnavailable` — a clean failure, but not support. A legacy
  `.ppt` did not route anywhere: OLE2 was sorted into Word or Excel and PowerPoint
  matched neither (VIP-109).

  `PptxEngine` wraps `python-pptx` the way `DocxEngine` wraps `python-docx`: slides in
  order, per-run font names as the signal the normalizer detects on, tables as table
  blocks. Legacy `.ppt` reaches it through LibreOffice, the same path `.doc` takes to
  DOCX.

  Ships in the existing `office` extra — `pip install "viparse[office]"`.

### Two structures a presentation has that a document does not

Both are places text goes missing quietly, which is a defect this library has now fixed
three times in other containers, so both are handled and tested rather than assumed.

**Shapes can be grouped, and a group can nest.** A walk over top-level shapes only would
drop everything inside one, and templates routinely put whole content areas in a group.

**Speaker notes are text nobody sees on the slide.** Included, after the slide's own
content and labelled with its number — the same reasoning as footnotes in 0.1.14. Text
that is in the file and silently dropped is the worst outcome; inlining it would put the
presenter's asides in the middle of the audience's text.

**Run fonts fall back to the paragraph's.** In a legacy presentation the font is often
set once on the paragraph rather than on each run, and reading the run alone loses the
signal the normalizer needs.

### Not measured

There is no legacy PowerPoint in
[viparse-corpus](https://github.com/TrizenX/viparse-corpus) — the collection sweeps
targeted `.doc`, `.pdf`, `.rtf` and `.xls`. The engine is verified against a real `.ppt`
produced by LibreOffice and against constructed fixtures, which is not the same as an
accuracy figure, and this release does not claim one.

Excel does have numbers now, from 28 real `.xls` documents: char 0.977, **diacritic
0.939**, syllable 0.948 — with the caveat, recorded in the corpus, that a spreadsheet
grid rendered two reasonable ways shifts the comparison in a way prose does not.

## [0.1.18] — 2026-08-02

### Added

- **A document handed back unconverted now says so.** Two real cases returned mojibake
  with nothing to indicate it (VIP-107).

  An RTF font table lists the fonts a document *declares* rather than the fonts applied
  to text, so the RTF engine emits no signal by design and a legacy `.rtf` came back
  raw. And a PDF can embed subsetted fonts that expose no legacy name — two of the five
  legacy PDFs in [viparse-corpus](https://github.com/TrizenX/viparse-corpus) do — so the
  font path missed them entirely.

  In both, the output reads as Vietnamese-shaped nonsense: nothing errors, nothing is
  empty, the length is right. A caller sees plausible output and has no reason to look
  further, which is the hardest failure to notice.

  A document that comes back unconverted is now scored the way `encoding="auto"` would
  have scored it, and if that would have found a legacy encoding the result carries:

  ```
  text looks like tcvn3 and was returned unconverted;
  pass encoding="tcvn3" or encoding="auto" to convert it
  ```

  Naming both the encoding and the fix, because a warning a caller cannot act on is
  noise. **It converts nothing itself**, and default behaviour is otherwise unchanged.

  Across the 76 documents in the corpus at default settings, 13 come back unconverted —
  11 RTF and 2 font-subset PDF. All 13 now warn; none is silent.

### Why it will not become noise

The check reuses `encoding="auto"`'s detection, so it inherits that path's guards: **a
document it warns about is one that opting in would actually have converted.** Warning
about a Spanish document would be advice to corrupt it. Tests hold that line for
Spanish, German and French, and for Unicode Vietnamese and plain ASCII.

Bounded to the first 4,000 characters — it runs on every document that was *not*
converted, which is most of them. A 248,000-character Unicode document normalizes in
36.6 ms with the check in place.

### Unchanged

No accuracy number moves: `.doc` TCVN3 0.975, VNI 0.998, `.rtf` 0.996, `.pdf` 0.999 with
`encoding="auto"`. This release changes what viparse *tells you*, not what it returns.

## [0.1.17] — 2026-08-02

### Fixed

- **Every `ư` was lost from a legacy PDF, and some `ã`.** A PDF stores glyph codes and
  the extractor resolves them through the font's encoding. For `.VnTime` that turns
  TCVN3's `0xAD` — the soft-hyphen slot, which is the letter `ư` — into
  `U+2212 MINUS SIGN`, and `0xB7` (`ã`) into `U+2219 BULLET OPERATOR` (VIP-105).

  ```
  nhµ n−íc         → nhà nước
  Thñ t−íng        → Thủ tướng
  Th«ng t−         → Thông tư
  céng hoµ x∙ héi  → cộng hoà xã hội
  ```

  **This is the third mechanism by which the same letter goes missing.** A legacy `.doc`
  loses `ư` through `<w:softHyphen/>` (0.1.9); a PDF loses it this way. 129 occurrences
  across the five legacy PDFs now in
  [viparse-corpus](https://github.com/TrizenX/viparse-corpus), where `ư` was the single
  largest source of mismatch against the transcripts.

  **Adjacency decides which occurrences are restored.** These documents are statistics
  tables, so a minus sign between digits is a minus sign — restoring every `U+2212`
  would trade one silent loss for another. Across the corpus PDFs no substituted
  codepoint sits between digits, and none of the 129 genuine ones lacks a letter
  neighbour.

  `U+2030 PER MILLE` is deliberately not included: `0,4 ‰` in a growth statistic is a
  real per mille sign. The test for membership is that every occurrence reads as a
  Vietnamese letter in context, not that the codepoint looks unusual.

  Applied only once a legacy encoding has been established, so Unicode text is never
  touched.

### Measured

The corpus now covers four real formats instead of one. `.doc` reaches the DOCX engine
through LibreOffice, so until this release only that path had real-document coverage.

| Format | documents | char | diacritic |
| --- | ---: | ---: | ---: |
| `.doc` TCVN3 | 44 | 0.969 | 0.975 |
| `.doc` VNI | 4 | 0.984 | 0.998 |
| `.rtf` | 11 | 0.991 | 0.996 |
| `.pdf`, `encoding="auto"` | 5 | 0.991 | **0.999** |
| `.pdf`, default | 5 | 0.986 | 0.975 |

### Two things those numbers say that the headline does not

**RTF needs `encoding="auto"`.** Its engine deliberately emits no font signal, because
an RTF font table lists the fonts a document *declares* rather than the fonts applied to
text. In default mode a legacy `.rtf` comes back as mojibake with no warning.

**Two of the five PDFs embed subsetted fonts that expose no legacy name**, so
default-mode detection misses them entirely. That is the gap between the two `.pdf` rows
— not the defect fixed above.

PowerPoint still has no engine: `.pptx` is recognised and then fails with
`EngineUnavailable`.

## [0.1.16] — 2026-08-02

### Fixed

- **`encoding="auto"` was a no-op on every PDF.** The gate for content detection was
  `method == "assumed-unicode"`, which means *no fonts at all* — and a PDF always
  reports fonts. The same text with no font information detected fine, so a font name,
  which says nothing about whether the text is Vietnamese, decided whether the caller's
  opt-in was honoured. Now gated on the fonts naming no *legacy* encoding (VIP-103).

- **`encoding="auto"` no longer corrupts other Latin languages.** 0.1.12 recorded under
  "Not fixed" that it turned Spanish `Señor` into `Seđor`. It no longer does, with or
  without fonts present.

  Frequency scoring cannot separate them: against the character model real TCVN3 gains
  **+0.244** while Spanish gains **+0.253** and German **+0.288**. Both beat genuine
  Vietnamese, so no threshold would work — raising it only starts rejecting real
  documents.

  What separates them is what the conversion *produces*, measured over the 48
  hand-transcribed documents in
  [viparse-corpus](https://github.com/TrizenX/viparse-corpus) against the same text run
  through the winning table:

  | | real Vietnamese (worst) | Spanish | French | German |
  | --- | ---: | ---: | ---: | ---: |
  | words > 7 letters | 0.008 | 0.095 | 0.222 | 0.375 |
  | words with `f/j/w/z` | 0.016 | 0.036 | 0.250 | 0.171 |

  Vietnamese writes each syllable as its own word, so long words barely exist, and the
  alphabet has no f, j, w or z. Both tests are applied, because a Spanish sample that
  happens to avoid f/j/w/z sits under the alien ceiling on its own.

### Unchanged

Accuracy is identical to 0.1.15 to three decimals — 0.981 diacritic over 43 TCVN3
documents, 0.998 over 4 VNI, 0.949 on the mixed-encoding one. The guards do not touch
real Vietnamese. Default mode is untouched; content detection remains opt-in.

### Known limitation

On a short sample the guards' rates are noisy, and they decline toward **leaving text
alone** rather than converting it. Detection is already unreliable on fragments for the
same reason: `laäp` on its own is read as VISCII, `Ñoäc laäp` as VNI. Pass a phrase, or
name the encoding.

**PDF, RTF and XLSX still have no real-document coverage.** The corpus is `.doc` only,
and `.doc` reaches the DOCX engine through LibreOffice — so that path is well tested
while the others are not. The bug above is the first one that gap was hiding.
PowerPoint has no engine at all; `.pptx` is recognised and then fails with
`EngineUnavailable`.

## [0.1.15] — 2026-08-02

The first release that is not about parsing. Both additions exist so an agent that has
never heard of viparse can still find it — by the **symptom** it is looking at rather
than by the product's name.

### Added

- **MCP server — `pip install "viparse[mcp]"`.** Run it with `viparse-mcp`, or
  `python -m viparse.mcp` (VIP-100).

  ```json
  { "mcpServers": { "viparse": { "command": "viparse-mcp" } } }
  ```

  Four tools. `repair_garbled_vietnamese` takes a **string**, not only a path, because
  most of the time the agent already has the broken text in context and has nothing to
  point a file-reading tool at. `identify_vietnamese_encoding` names the encoding
  without changing anything and returns a preview, so its verdict can be judged rather
  than trusted. `read_vietnamese_document` is `load()` over a path. `viparse_version`
  is for bug reports.

  A thin wrapper: no parsing logic, and the safety limits, path handling and layered
  options are whatever `viparse.load` already enforces.

  `mcp` is deliberately **not** in the `all` extra — `all` is about parsing capability,
  and installing every format handler should not pull in a server runtime.

- **Agent skill — `skills/garbled-vietnamese-text/SKILL.md`.** Covers recognising each
  encoding, converting with and without a file, and the traps: never convert text that
  is already Unicode, a font name is not proof, one document can be two encodings, and
  detection needs a phrase rather than a four-character fragment (VIP-101).

  Copy it into `.claude/skills/` or your agent's equivalent. Its tests execute every
  conversion the document claims, read out of the Markdown table rather than
  duplicated, so the two cannot drift.

### Why both are written around the symptom

An agent never thinks *"I should use viparse"* — it has never heard of it. It
encounters `B¸o c¸o tµi chÝnh` in a file it just read and needs something that
recognises **that**. So the tool descriptions and the skill frontmatter contain the
mojibake itself, the font names and the encoding names, and never lead with the product
name. Tests assert that property, because it is easy to lose in an edit that is only
trying to tighten wording.

### No parsing behaviour changed

Accuracy is unchanged from 0.1.14: 0.981 diacritic over 43 TCVN3 documents, 0.998 over
4 VNI, 0.949 on the mixed-encoding one.

## [0.1.14] — 2026-08-02

### Added

- **Footnotes and endnotes are read.** They live in their own OOXML parts
  (`word/footnotes.xml`, `word/endnotes.xml`), so nothing that walks the document body
  reached them. On one real document that was 1,062 characters — the entire bibliography
  — missing with no warning (VIP-98).

  Placed **after the body**, not inlined at the reference point. That is where Word
  itself keeps them: in the legacy `.doc` this was measured on, the footnote text follows
  the closing `./.`. Splicing a citation into the middle of the sentence that cites it
  would corrupt exactly the sentence boundaries downstream chunking depends on.

  Word's two housekeeping notes in each part — the rule drawn above the notes, and the
  one drawn when they continue onto the next page — are skipped, so a document with a
  single footnote does not gain two spurious blocks. A malformed notes part is skipped
  rather than allowed to fail the extraction; the body is worth more than the citations.

### Measured

TCVN3 diacritic accuracy over 43 real documents: **0.977 → 0.981**.

### Known limitation, and it is not this library's

The document that motivated this fix still scores 0.679. What holds it there is
**LibreOffice's own `.doc` → `.docx` conversion, which loses about 5,642 characters** —
passages present in the original appear in neither `document.xml` nor `footnotes.xml`,
so they are gone before viparse is handed anything.

On that document roughly **18% of the achievable ceiling belongs to the conversion step,
not to viparse**. Worth knowing before a legacy-`.doc` score is read as a parser score.

## [0.1.13] — 2026-08-02

Two extraction fixes, both found by real documents rather than fixtures, and both
silent: the output looked like correct Vietnamese while a large part of the document
was missing or unconverted.

### Fixed

- **Tracked insertions were dropped entirely.** `python-docx`'s `paragraph.runs` returns
  only *direct* `w:r` children of `w:p`, so a run inside `<w:ins>` was invisible — and
  LibreOffice writes tracked insertions when converting a legacy `.doc` that carries
  them. In one real government document 10,473 of 25,377 characters, **41% of the body**,
  were discarded without a warning (VIP-95).

  Both the block text and the per-run font segments now walk `w:r` descendants in
  document order, so they stay in step for mixed-encoding paragraphs. Also reached:
  `w:hyperlink`, `w:smartTag`, `w:moveTo`, `w:sdtContent`.

  Runs under `w:del` and `w:moveFrom` stay excluded. Those hold what a tracked change
  *removed*; including them would resurrect deleted sentences, and text that is wrong is
  worse than text that is short.

  **Re-run any `.docx` or legacy `.doc` corpus that has been through review.**

- **A block whose font name is unrecognised is now read by its bytes.** An unknown font
  produced `encoding=None`, which the planner read as *leave this text alone* — an
  absence of evidence treated as evidence the text is Unicode. A Lâm Đồng planning
  document carries 174,646 characters under `VNSTCVN3`, a real TCVN3-era font matching
  none of `.Vn*`, `VNI-*`, `VPS*` or `ABC*`, and 93% of it was returned unconverted at
  0.084 diacritic accuracy (VIP-96).

  Recognising the font name would have been worse, not better: **109,211 of those
  characters are VNI, not TCVN3.** The document was assembled from sections typed on
  different machines with one font applied across all of them, so the name is actively
  wrong for most of what it covers.

  Scoped deliberately. Detection runs per *block*, not per run — a per-run pass read
  `MôC LôC` as VNI. Blocks under 24 characters inherit the previous block's verdict
  rather than guess. And the fallback needs **both** `encoding="auto"` and a legacy font
  signal somewhere in the document, so an unrecognised font still protects
  non-Vietnamese text: `Señor` does not become `Seđor`.

### Measured

Against hand-written transcripts of 48 real documents in
[viparse-corpus](https://github.com/TrizenX/viparse-corpus):

| Subset | documents | diacritic, 0.1.12 | diacritic, 0.1.13 |
| --- | ---: | ---: | ---: |
| TCVN3 | 43 | 0.959 | **0.977** |
| VNI | 4 | 0.998 | 0.998 |
| mixed TCVN3+VNI | 1 | 0.084 | **0.949** |

The mixed document needs `encoding="auto"`; the rest are default-mode.

### Known limitation

Footnotes are a separate OOXML part (`word/footnotes.xml`) that the engine does not
read. On the document above that is 1,062 characters. Whether footnote text belongs
inline in body text is a design question, still open.

Separately, LibreOffice's own `.doc` → `.docx` conversion can lose text before viparse
sees it — about 5,642 characters on that same file. That is upstream of this library,
and worth knowing before a legacy-`.doc` score is read as a parser score.

## [0.1.12] — 2026-08-01

### Fixed

- **Uppercase VISCII was never detected, and its letters were silently deleted.**
  Content detection ran on cleaned text, and cleanup strips control characters. VISCII
  keeps **38 of its 103 letters in the control ranges** — 6 in C0 (`Ẳ Ẵ Ẫ Ỷ Ỹ Ỵ`) and
  32 in C1 (`Ạ Ộ Ế Ề Ệ Ị Ọ Ủ Ụ` among them) — so over a third of a VISCII document was
  deleted before scoring. VISCII scored near zero on its own text, `encoding_detected`
  came back `None`, and the caller got mojibake with letters missing: `CỘNG` → `CNG`,
  `CHỦ` → `CH` (VIP-93).

  The split is by case, which is why it survived so long. VISCII keeps its *lowercase*
  letters in `0xA0–0xFF` and only its uppercase ones in C0/C1, so the existing detection
  test — `"Việt Nam độc lập"`, all lowercase — passed throughout. The case that failed
  was `"CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM"`, the line every Vietnamese administrative
  document opens with.

  **Affects `encoding="auto"` only.** Explicit `encoding="viscii"` already worked, since
  conversion runs before cleanup on that path. Font-signal detection is unaffected — and
  cannot find VISCII regardless, because VISCII is a charset rather than a font hack and
  declares no distinctive font name.

  **Re-run any VISCII corpus parsed with `encoding="auto"` on 0.1.11 or earlier.**

### Not fixed

`encoding="auto"` still reads Spanish `"señor"` as VNI and returns `"seđor"`. That
behaviour is unchanged by this release and is the documented trade-off of an opt-in path
where the caller asserts the source is legacy Vietnamese. Pass an explicit `encoding=`
when the source language is not certain.

## [0.1.11] — 2026-08-01

### Added

- **VNI is usable.** The conversion table went from **6 entries to 130** — the whole
  Vietnamese repertoire bar four letters. Before this, viparse identified VNI correctly
  and then had almost nothing to convert it with: a VNI document came back at 0.307
  diacritic accuracy against TCVN3's 0.987 (VIP-91).

  Derived against the VNI documents in
  [viparse-corpus](https://github.com/TrizenX/viparse-corpus) — 53,715 characters over
  four real administrative documents — not transcribed from a layout chart. Each entry
  carries its occurrence count in that corpus, or the marker `derived`: 104 are observed
  directly (`ö` → ư 927 times, `ñ` → đ 788), and 26 come from two rules that are
  themselves observed dozens of times.

### Known limitation

**`ẳ ẵ Ẳ Ẵ` are not mapped, deliberately.** No collected VNI document contains any of
the four, and every other modifier character that follows a base vowel in that corpus
is mapped — so these are unobserved, not overlooked. Unmatched input passes through
unchanged, so a document containing `ẳ` returns it unconverted rather than silently
wrong. A test names all four; it is what should fail when such a document turns up.

Filling them by symmetry with the ắ/ằ/ặ row would be easy, and it is exactly how the
`a½` entry fixed in 0.1.10 came to be written.

### A note on the accuracy figure

The corpus reports VNI diacritic accuracy rising 0.307 → 0.998 with this table. **That
number is circular and is not a quality claim.** The ground truth for those documents
was produced with the table this one inverts, so it would read 0.998 even if every
mapping were wrong. It shows the entries transferred intact, nothing more. The evidence
that the table is right is the per-entry occurrence counts and the fixed administrative
formulas whose Unicode reading is externally known.

## [0.1.10] — 2026-08-01

### Fixed

- **VNI grave was mapped to a TCVN3 byte.** The table read `a½` for à. `0xBD` is TCVN3's
  ẵ and has no role in VNI, which writes à as `aø` — 211 occurrences across the VNI
  documents in [viparse-corpus](https://github.com/TrizenX/viparse-corpus) against zero
  for `a½`.

  Not a cosmetic error. The wrong entry occupied the grave slot, so `aø` was absent from
  the table and à was never converted at all. On the two real VNI documents, diacritic
  accuracy goes **0.234 → 0.291** and syllable 0.342 → 0.395 (VIP-89).

  TCVN3 is unaffected.

### Known limitation

**VNI is still mostly unconverted.** The table holds five sequences plus `đ` where the
encoding needs roughly fifty, so a VNI document comes back at **0.246** diacritic
accuracy. Detection is not the gap — viparse identifies VNI at 0.95 confidence and then
has almost nothing to convert it with. TCVN3, by comparison, is at 0.987.

Closing it needs more VNI source documents than the two collected so far. Filling the
remaining rows by symmetry is precisely how the `a½` entry came to be written, and that
mistake has now been made twice in this project.

## [0.1.9] — 2026-08-01

### Fixed

- **Every `ư` was deleted from legacy `.doc` files.** 848 of 848 occurrences across ten
  real Vietnamese government documents — `được`, `người`, `trường`, `nước` all came back
  a letter short, with nothing logged.

  A `.doc` stores `0xAD`, which TCVN3 reads as `ư`. Converting to `.docx` encodes a soft
  hyphen as the element `<w:softHyphen/>` rather than a character, and `python-docx`
  concatenates only text nodes — so the letter was gone before the encoding table saw
  it. Table cells were a second path to the same loss (VIP-87).

  **Re-run any corpus parsed with 0.1.8 or earlier.** The loss was silent, and `ư` is one
  of the most common letters in Vietnamese.

End-to-end diacritic accuracy against hand-written transcripts of that corpus: **0.949 →
0.999**.

## [0.1.8] — 2026-08-01

The first release since 0.1.5 to change behaviour rather than metadata.

### Fixed

- **TCVN3 conversion was one sixth complete.** The table held 12 of the 74 mappings
  the encoding needs — the `a` vowel family plus `đ` — so real documents came back
  with `à á ả ã ạ ă đ` restored and `ế ị ộ ứ ổ ơ ề` untouched. Measured against ten
  hand-transcribed Vietnamese government documents, diacritic recovery was 32.8%.

  The source column is now validated against a corpus of 31 TCVN3 documents published
  by government bodies between 1998 and 2009, by aligning byte sequences with the
  fixed phrases such documents always carry. Every entry but one is backed by an
  observed occurrence (VIP-85).

  Anyone parsing TCVN3 with 0.1.7 or earlier should re-run their corpus: text that
  looked partly converted was silently keeping most of its diacritics as Latin-1
  bytes.

### Note for anyone relying on content-based detection

Completing one table narrows the margins between all of them. A complete TCVN3 table
trial-converts VISCII bytes into something Vietnamese-shaped enough to land within
0.011 of the correct reading on a short phrase, at which point detection declines to
choose rather than guessing. Over a sentence the gap is ~0.09. Content detection
remains opt-in for exactly this reason; font signals are unaffected.

## [0.1.7] — 2026-08-01

Metadata only — `src/` is byte-identical to 0.1.6. Cut so PyPI stops publishing
identity that points at the wrong place, since package metadata is what indexes
and crawlers read.

### Fixed

- Every URL in `[project.urls]` still named the pre-transfer `minhtridinh-kayden`
  account, so PyPI — and piwheels, which mirrors it — kept advertising a repo the
  project no longer lives in. `Homepage` now points at the site, and `Issues` is
  published for the first time (VIP-81).
- The `author` field held a bare handle with no contactable address and no full
  name, leaving anything that reads the metadata to infer one. It now carries the
  author's name and a project address (VIP-81, VIP-82).

### Added

- `CITATION.cff`, validated against schema 1.2.0. It is the only metadata here
  that separates family from given names, and GitHub renders it as a "Cite this
  repository" button (VIP-82).

## [0.1.6] — 2026-07-28

Documentation and tooling only — `src/` is byte-identical to 0.1.5, so upgrading changes
no behaviour. It is cut so PyPI, which renders the README as the project page, stops
serving incomplete install instructions.

### Fixed

- The installation section omitted the `rtf`, `langchain` and `llamaindex` extras and never
  stated the Python floor, so anyone reading the PyPI page could not discover three of the
  seven extras and had no version requirement to check against (VIP-77).

### Changed

- The README now documents the `route → extract → normalize → structure` pipeline, how
  encoding detection picks a charmap, and where viparse sits next to general-purpose
  loaders. It links the project website at https://viparse.trizenx.com (VIP-77).
- `ruff` and `mypy` are capped to a minor series. Both gate CI, and an unpinned release of
  either turns `quality` red on unrelated work — ruff 0.16 did exactly that and blocked
  every open PR for three days (VIP-78, VIP-79).

## [0.1.5] — 2026-07-19

### Added

- **RTF support** — a new `.rtf` text-extraction engine (behind the `viparse[rtf]` extra,
  wrapping the pure-Python `striprtf`), detected by magic bytes (a leading UTF-8 BOM is
  tolerated). A legacy-encoded `.rtf` is normalized like any other font-less source — via
  content detection (`encoding="auto"`) or an explicit `encoding=` override. The engine
  deliberately does not infer an encoding from the RTF font table, which lists *declared*
  rather than *applied* fonts and could otherwise convert a Unicode body through a legacy
  charmap (VIP-75).

## [0.1.4] — 2026-07-19

### Changed

- **Per-run encoding detection** — mixed-encoding detection now works at *run* granularity,
  not just per block: a single paragraph that mixes a legacy `.Vn*`/`VNI-` run with a
  Unicode run is converted run-by-run, so a Unicode run (e.g. one containing `®`) is no
  longer mangled by a neighbour's legacy charmap. A block is only split when its runs
  actually disagree, so a legacy multi-character form is never severed at a run boundary;
  single-encoding and per-block output stay byte-for-byte identical (VIP-72).

### Added

- **VPS legacy encoding** — added the VPS (Vietnamese Professional System) → Unicode
  conversion table alongside TCVN3, VNI, and VISCII, selectable via an explicit
  `encoding="vps"` override. VPS shares VISCII's Latin-1 surface bytes, so it is
  intentionally excluded from content-frequency auto-detection to avoid mis-converting
  genuine VISCII text. The 112-byte mapping is cross-verified against four independent
  sources (vietunicode, the Encode::VN `.ucm`, `vietnameseConverter`, and
  `py-unicode-convert`) (VIP-71).

## [0.1.3] — 2026-07-18

### Fixed

- **Per-block encoding detection for mixed-encoding documents** — a document that mixes a
  legacy `.Vn*`/`VNI-` run with already-Unicode runs is now detected and converted per block,
  by each block's own font signal, instead of applying one file-wide verdict. A Unicode run
  containing a character that is also a legacy surface byte (e.g. `viparse® 2026`) is no longer
  corrupted (`viparseđ 2026`), while the adjacent legacy run still converts. Single-encoding
  documents are unaffected — their output is byte-for-byte identical (VIP-65).

## [0.1.2] — 2026-07-12

Dependency compatibility only — no code or behavior changes.

### Changed

- **Widened dependency upper bounds** so viparse installs alongside newer major releases:
  `pillow<13` (extra `ocr`), `langchain-core<2` (extra `langchain`), and `reportlab<6`
  (dev only). Verified against pillow 12, langchain-core 1.x, and reportlab 5 (#47, #48).

## [0.1.1] — 2026-07-12

Documentation and packaging only — no code or behavior changes.

### Added

- **MIT license** — added a `LICENSE` file and declared `license = "MIT"` in the package
  metadata (VIP-62).
- **README** — installation instructions (`pip install viparse` and extras), a usage section,
  and released status linking PyPI (VIP-62).
- **PyPI publishing** — a GitHub Actions workflow publishes to PyPI via Trusted Publishing
  (OIDC, no stored token) when a release is published (VIP-61).

### Fixed

- **Project URLs** — corrected the repository URL and added Homepage / Changelog links shown on
  the PyPI page (VIP-61).

## [0.1.0] — 2026-07-12

First tagged release. Covers the full M0–M5 feature set (VIP-1 … VIP-59).

### Added

- **Public API** — `viparse.load(source, *, output, encoding, ocr, normalize, max_bytes,
  cache, chunk, settings)` and lazy `viparse.load_batch(...)`, returning Unicode-**NFC**
  `Document`s as markdown / text / json.
- **Layered configuration** — `output` / `encoding` / `ocr` / `normalize` / `max_bytes` resolve
  from function args → `VIPARSE_*` env vars → a `viparse.toml` file → the built-in defaults. A
  validating `Settings` (via `load_settings()`) raises `ConfigError` on a bad value.
- **RAG chunking** — opt-in `chunk=ChunkOptions(max_tokens, overlap_tokens)` splits a document
  into retrieval-sized, section-aware `Chunk`s (never splitting a table row) with per-chunk
  `section` / `page` / `sheet` metadata and an ordinal `index`.
- **Framework integrations** — `to_langchain_documents(doc)` / `to_llamaindex_documents(doc)`
  map a `Document` (chunk-aware) onto LangChain / LlamaIndex document types, provenance
  flattened into their `metadata`. Lazy behind `viparse[langchain]` / `viparse[llamaindex]`.
- **CLI** — `viparse <files> -o md|text|json` (globs, directories, `--out`,
  `--encoding`/`--ocr`/`--normalize`) and `viparse doctor` (engine + binary availability).
- **Extraction engines** — DOCX, XLSX, digital PDF, scanned PDF via OCR (`viparse[ocr]`),
  and legacy binary `.doc`/`.xls` via LibreOffice — all thin adapters behind extras so the
  `core` install stays dependency-free.
- **Vietnamese normalization (the moat)** — legacy **TCVN3 / VNI / VISCII** → Unicode NFC,
  with font-signal detection, opt-in content-based detection (`encoding="auto"`), and text
  cleanup. Output is always NFC.
- **Structured output** — headings, GFM tables, and a versioned JSON schema
  (`viparse.SCHEMA_VERSION`).
- **Untrusted-input safety** — configurable file-size limit, zip-decompression-bomb guard,
  and per-engine process timeouts (`UnsafeInput`).
- **Caching** — content-hash `MemoryCache` / `DiskCache` to skip re-parsing unchanged files.
- **Parallel batch** — `load_batch(..., workers=N)` with bounded concurrency and per-source
  error isolation.

[Unreleased]: https://github.com/TrizenX/viparse/compare/v0.1.19...HEAD
[0.1.19]: https://github.com/TrizenX/viparse/compare/v0.1.18...v0.1.19
[0.1.18]: https://github.com/TrizenX/viparse/compare/v0.1.17...v0.1.18
[0.1.17]: https://github.com/TrizenX/viparse/compare/v0.1.16...v0.1.17
[0.1.16]: https://github.com/TrizenX/viparse/compare/v0.1.15...v0.1.16
[0.1.15]: https://github.com/TrizenX/viparse/compare/v0.1.14...v0.1.15
[0.1.14]: https://github.com/TrizenX/viparse/compare/v0.1.13...v0.1.14
[0.1.13]: https://github.com/TrizenX/viparse/compare/v0.1.12...v0.1.13
[0.1.12]: https://github.com/TrizenX/viparse/compare/v0.1.11...v0.1.12
[0.1.11]: https://github.com/TrizenX/viparse/compare/v0.1.10...v0.1.11
[0.1.10]: https://github.com/TrizenX/viparse/compare/v0.1.9...v0.1.10
[0.1.9]: https://github.com/TrizenX/viparse/compare/v0.1.8...v0.1.9
[0.1.8]: https://github.com/TrizenX/viparse/compare/v0.1.7...v0.1.8
[0.1.7]: https://github.com/TrizenX/viparse/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/TrizenX/viparse/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/TrizenX/viparse/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/TrizenX/viparse/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/TrizenX/viparse/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/TrizenX/viparse/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/TrizenX/viparse/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/TrizenX/viparse/releases/tag/v0.1.0
