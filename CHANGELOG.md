# Changelog

All notable changes to viparse are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.29] — 2026-08-05

### Added

- **`VietnameseDocumentLoader`** — a LangChain `BaseLoader` — and **`ViparseReader`** — a
  LlamaIndex `BaseReader` (VIP-125):

  ```python
  from viparse.integrations import VietnameseDocumentLoader, ViparseReader

  docs = VietnameseDocumentLoader("bao_cao_cu.doc").load()
  documents = ViparseReader().load_data("bao_cao_cu.doc")
  ```

  viparse already had `to_langchain_documents` / `to_llamaindex_documents`, and they were
  the wrong shape for adoption: a **converter** is only ever reached by someone who has
  already chosen viparse, while a **loader** is reached by someone who was already writing
  a pipeline and needed a Vietnamese document read correctly. Only the second can be found
  by a stranger.

  Both take the same options as `load()`, both stream (`lazy_load` is a generator, so a
  large document is not materialised first), and both still import their framework lazily
  — `import viparse.integrations` pulls in neither.

### Why this instead of upstream PRs

The roadmap said to open PRs against `langchain-community` and the LlamaHub reader
registry. Checked 2026-08-05: both projects have closed that path.

> LlamaIndex `CONTRIBUTING.md`: *"we are no longer accepting new integration packages in
> this repository… PRs that add a new `pyproject.toml` will be automatically closed."*
>
> LangChain contributing guide: *"New integrations are not accepted as PRs to
> `langchain-ai` repos — they must be published independently to PyPI or npm."*

The plan's acceptance criterion was "their CI passing", which is unreachable when a bot
closes the PR before CI runs. Being the integration is the reachable version of being in
one.

## [0.1.28] — 2026-08-04

### Measured

**A third real scan.** The sweep widened from 200 candidate URLs to 2,300 across every
domain in the corpus's `domains.txt`, producing 14 more scanned PDFs on top of the
original 11 — **25 collected in total**, of which 3 are transcribed and scored (VIP-124).

| document | char | diacritic |
| --- | ---: | ---: |
| `2005-mpi-qd837` | 0.991 | 0.988 |
| `2005-mpi-tt01-ptbv` | 0.981 | 0.983 |
| `2015-molisa-ttr-nd51` | 0.979 | 0.954 |
| **all three** | **0.983** | **0.973** |

Up from 0.968 on two. Rendered pages score 0.990, so a real page costs roughly two points.
Still a floor rather than a benchmark, and the corpus carries the live figure as more are
transcribed.

The bottleneck has moved and is worth naming: collection is a background job — a CDX
query, a parallel download, a screen that keeps only PDFs with no text layer. Reading a
page and typing what it says is not, and it is the only thing between 3 documents and 30.

No library behaviour changed; this updates the figures the package states about itself.

## [0.1.27] — 2026-08-04

### Corrected

**Every OCR figure published in 0.1.26 was wrong**, and by a lot. The cause was a defect in
the corpus scorer, not in viparse (VIP-123).

`score.py` aligns two texts by splitting them into segments on sentence punctuation, and
for a region where the two sides differ it paired them **positionally**. That breaks the
moment they segment differently — and they do, because segmentation depends on punctuation
the parser may have misread. On a real scan, OCR lost one `:`; every following segment
shifted by one, and a 284-character segment was scored against `""`. Raw similarity of the
two texts was 0.9904 and the metric reported 0.578.

| | published in 0.1.26 | actual |
| --- | ---: | ---: |
| OCR, rendered pages | 0.933 | **0.990** |
| OCR, rendered, degraded | 0.816 | **0.986** |
| OCR, real scans | not measured | **0.968** |
| conversion path, legacy corpus | 0.982 | **0.986** |
| baseline, no conversion | 0.019 | **0.019** |

Two claims from 0.1.26 are withdrawn:

- **"OCR is the weakest path in viparse."** It is not — 0.990 against 0.986 for
  conversion.
- **"Two subsets are needed because the renderer cannot draw a spreadsheet."** All 96
  documents score 0.990 and prose-only 0.992. Tabular transcripts segment most unlike OCR
  output, so they were where the defect bit hardest.

The baseline did not move, which is the reassuring part: the floor was never in question,
so the gap this product is about is intact.

### Measured

**The first real scans.** Two genuine scanned Vietnamese government documents,
hand-transcribed from the image *before* OCR was run on them: **0.984** char, **0.968**
diacritic. Eleven scans were found by screening 200 archived government PDFs for the
absence of a text layer; nine were rejected, all but one for personal data.

Two documents is a floor under the rendered figures, not a benchmark.

### Changed

- The figures are corrected in all five places they appear: both READMEs, the engine
  docstring, the test module docstring, and `viparse doctor`.

No library behaviour changed. This release exists because 0.1.26 shipped wrong numbers to
PyPI.

## [0.1.26] — 2026-08-04

### Measured

**OCR has a number, and it is the worst one in this project** (VIP-122). It was advertised
in six places and measured in none: every OCR test mocked Tesseract, no scanned document
existed in any published benchmark, and this project had never executed the engine against
a real Tesseract.

Scoring OCR needs a page image whose correct text is already known. The corpus has no
scans — but it has 96 hand-written transcripts, and rendering one back to a page image
produces exactly that pair at no cost in new transcription.

| render | documents | char | **diacritic** | syllable |
| --- | ---: | ---: | ---: | ---: |
| clean, all | 96 | 0.874 | **0.933** | 0.872 |
| clean, prose only | 65 | 0.926 | **0.967** | 0.938 |
| degraded, all | 96 | 0.749 | **0.816** | 0.748 |
| degraded, prose only | 65 | 0.856 | **0.898** | 0.866 |

The conversion path scores **0.982** on the same documents. **0.967 is a ceiling**: a
perfectly rendered page, no skew, no sensor noise, no paper texture, in a font Tesseract
finds easy. No real scanned Vietnamese document has been measured at all.

The errors are almost entirely **tone marks, in both directions** — a hook invented on
bare `i` 93 times; the tone dropped from `ề`/`ầ`/`ồ` 60 times; `I` read as `l` or `|` 19
times. They land precisely on the marks this product exists to preserve. The first run
turned `quý II` into `quý lI`.

Method, both subsets and every caveat:
[viparse-corpus/ocr](https://github.com/TrizenX/viparse-corpus/tree/main/ocr).

### Changed

- The "OCR is unmeasured" wording added in 0.1.25 is replaced by the figures, in all five
  places it appeared: both READMEs, the engine docstring, the test module docstring, and
  `viparse doctor` — which now reads `diacritic accuracy 0.967 at best, 0.898 on degraded
  pages — the weakest path here`.

No library behaviour changed in this release. It exists because the claim shipped to PyPI
in 0.1.25 said the accuracy was unknown, and that is no longer true.

## [0.1.25] — 2026-08-04

### Added

- **Page images are readable: `.png`, `.jpg`, `.tif`** (VIP-121). Until now they raised
  `UnsupportedFormat` at the router, before any engine saw them — the format detector
  knew four magic signatures and none was an image.

  This is how a great many old Vietnamese documents actually exist: a flatbed scan saved
  as archival TIFF, or a photograph taken with a phone. A **multi-page TIFF** is walked
  frame by frame, because that is what a digitised archive is and reading only the first
  page would drop the rest in silence.

  ```python
  viparse.load("scan.jpg")  # ocr=True is implied — an image has no text layer
  ```

- **Image OCR no longer needs poppler.** `pdf2image` is imported only for a PDF, so a
  machine with Tesseract but no poppler can still read an image. The two missing-binary
  errors name their own binary rather than sharing one message.

### Changed

- An image turns `ocr` on by itself when the caller left it unset. An image *is* a scan —
  there is no text layer it could have instead — and OCR is the only engine that reads
  one. Without this, a `.jpg` went down the plain-engine path and came back with "no
  engine registered for content type 'image/jpeg'", which names the wrong problem.
  Passing `ocr=False` on an image now says why that cannot work.
- `viparse doctor` notes beside the OCR engine that its accuracy is unmeasured. That is
  the screen where someone decides what they can rely on, and "available" would otherwise
  read as "measured".

### Not measured, and said plainly

**This release ships a feature on a code path that has never been executed.** Every OCR
test in this project mocks Tesseract; no scanned document exists in either published
benchmark; no OCR accuracy figure has ever been taken. Adding image support does not
change any of that — it adds a second route into the same unverified engine.

That is a deliberate choice made with the risk stated rather than discovered later, and
it is now written in `README.md`, `README.vi.md`, the engine's own docstring, the test
module's docstring, and `viparse doctor`. Every other claim this project makes has a
number behind it. This one does not, and it is labelled everywhere it appears.

Measuring it needs Tesseract plus the `vie` language data installed. The corpus already
holds 96 hand transcripts, so the measurement itself costs no new transcription: render a
document to page images, OCR it, score against the transcript that already exists.

## [0.1.24] — 2026-08-04

Three defects in shipped code, none of them visible in the text output, all three found
by measuring ordinary Unicode documents for the first time (VIP-120).

Every number this project published was measured on legacy-encoded files. That is the
moat and the right thing to measure — but it is not what most callers will hand over, and
twenty minutes of unmeasured spot-checking found three things wrong.

### Fixed

- **PowerPoint slide titles were never headings**, since the engine shipped in 0.1.19.
  `shape is slide.shapes.title` never matched: python-pptx builds a fresh proxy on every
  access, so `slide.shapes.title is slide.shapes.title` is itself `False`. The title was
  always present and in the right place, just unmarked — so no presentation ever had a
  section for chunking to work on. Compared by `shape_id` now.

- **A table split across chunks lost its header row.** The header stayed with the
  previous chunk and the continuation was bare data: `Tăng trưởng GDP  5,66%  6,42%`,
  with nothing saying which quarter is which. Retrieval surfaces such a chunk on its own
  and it looks perfectly usable. Continuations now repeat the header, flagged with
  `table_header_repeated` in the chunk metadata, and the repeat is charged to the token
  budget rather than quietly overflowing it.

- **A table split across PDF pages lost its header too**, for a different reason: it came
  back as two blocks and the second had no header row at all. Rejoined now, under narrow
  conditions — the continuation must open its page, start near its top, directly follow a
  table, and match its column count. A wrongly-joined table still contains every row; a
  wrongly-split one loses its header, so the bias is deliberate.

### Measured

A [structure benchmark](https://github.com/TrizenX/viparse-corpus/tree/main/structure)
now exists, and unlike the accuracy corpus it cannot be circular: it plants labelled
paragraphs, headings and tables in generated documents and counts what comes back, so
there is no transcript to agree with.

| document | order | completeness | headings |
| --- | ---: | ---: | ---: |
| `.docx`, `.xlsx`, `.pptx` | 1.000 | 1.000 | **1.000** |
| one-column PDF | 1.000 | 1.000 | **0.000** |
| two-column PDF | **0.600** | 1.000 | **0.000** |

The legacy corpus is unchanged at **0.978** char / **0.982** diacritic over 96 documents,
which is the point: none of this touched conversion.

### Documented rather than fixed

Both remaining zeros are now stated outright in the README. A PDF has no headings, so
every chunk from one carries an empty `section`; and a multi-column PDF is read across
the page rather than down the columns, so paragraph 1 is followed by paragraph 19.

Recovering columns means detecting them, which is layout analysis, which viparse does not
do — the whitespace table-detection experiment took the corpus from 0.991 to 0.493 and
was not shipped. The intended answer for multi-column PDFs is a layout-aware loader with
`viparse.fix()` over its output.

### Added

- **`README.vi.md` — the documentation in the language its users speak.** Every public
  word about viparse was English, while the people holding a `.doc` in `.VnTime` search
  in Vietnamese: *chuyển bảng mã TCVN3 sang Unicode*, *file Word bị lỗi phông*. It is
  written natively rather than translated, and anchors the product to the one thing
  every Vietnamese developer already knows — Unikey's *Công cụ → Chuyển mã* — because
  that locates it in one sentence.
- **`tests/test_readme.py` runs the examples both READMEs claim**, the way
  `tests/test_skill.py` already does for the agent skill. It matters more for the
  Vietnamese file: the English README is read by everyone, so a wrong example there gets
  noticed, while the other can drift unchecked. The count assertion earned itself
  immediately — a greedy regex silently matched two of three examples, which would have
  passed as a green suite.

## [0.1.23] — 2026-08-04

### Added

- **`viparse.fix(text)` — the normalization pass, as an API.** The README has always
  said viparse can be used *"as a normalization pass over text another loader
  produced"*. The API did not offer one. Reaching it meant constructing a
  `RawExtraction` and a `LoadOptions` and calling `VietnameseNormalizer` directly, and
  four places in this project did exactly that: the MCP server, the agent skill, the
  landing page's TypeScript port, and `api.py` itself (VIP-117).

  ```python
  docs = [viparse.fix(doc.page_content) for doc in loader.load()]
  ```

- **`viparse.detect_text_encoding(text)`**, for callers who want to look before
  converting. Returns an encoding name, or `None` when none was found.

  `encoding` defaults to `"auto"` in `fix()`, unlike `load()`, where content detection
  is opt-in because a caller handing over a *file* may not know what is in it. Someone
  calling a function named `fix` on a string they are looking at has already made that
  assertion.

### Changed

- The MCP server and the agent skill now use the new API; the skill's example goes from
  eleven lines to one.
- `identify_vietnamese_encoding` no longer returns `confidence`. Content-detection
  confidence is a scaled margin; what a caller can act on is whether an encoding was
  named at all.
- The README's accuracy section said a published benchmark was "planned for v0.2". It
  exists — 96 documents, five formats, **0.982** against a **0.019** baseline. It now
  states that, and says plainly that no other tool has been run against the corpus, so
  it is not a comparison.

### Measured

No conversion behaviour changed: `fix()` runs the same normalizer over the same tables,
so the corpus stands at **0.978** char, **0.982** diacritic over 96 documents.

> **Corrected after publication.** This entry first read *108 documents* and *0.983*.
> Both were wrong, and the corrected figures above are from
> [`viparse-0.1.23-full-corpus.json`](https://github.com/TrizenX/viparse-corpus/blob/main/results/viparse-0.1.23-full-corpus.json),
> the first results file published for a release since 0.1.20. See
> [RESULTS.md](https://github.com/TrizenX/viparse-corpus/blob/main/RESULTS.md) for what
> each number was and where it came from. The 0.1.22 entry below inherits the same wrong
> diacritic figure and is left as written, because it is a record of what was believed at
> the time.

## [0.1.22] — 2026-08-04

### Fixed

- **A foreign-language block inside a legacy document was converted anyway.** Content
  detection returned the same `"assumed-unicode"` verdict for two different findings:
  *not enough evidence to tell*, and *the text converted well and then read as another
  language* (VIP-115).

  The second is a positive result, and a caller can act on it. A block that declined for
  want of evidence should take its neighbour's verdict — an encoding changes at a section
  boundary rather than mid-document. A block that is actively Spanish should not, and
  until now it did: a Spanish table beside a Vietnamese one in the same workbook
  inherited TCVN3 and came back as `Seđor`.

  The guard rejection now reports `method="content-not-vietnamese"`, and the per-block
  fallback suppresses inheritance only for that.

### The second attempt at this, and why the first was wrong

0.1.21 tried treating *every* declined detection as "not Vietnamese" and took the corpus
from 0.980 to **0.967** — most declines are ordinary Vietnamese blocks that simply did
not score well enough to be sure. The distinction had to come from the detector rather
than from a guess at the call site, which is what this release does.

### Measured

Corpus unchanged: **0.978** char, **0.983** diacritic over 96 documents.

That is the right outcome, not a disappointing one. The case fixed here — a
foreign-language block inside a legacy Vietnamese document — does not occur in the
corpus, so a number that *moved* would have meant something else had broken. Both halves
of the distinction have a test.

## [0.1.21] — 2026-08-02

### Fixed

- **Tables were invisible to content detection.** A table block carries `rows` and no
  `text` key, and the per-block content fallback asked it for `block.get("text", "")`.
  It got the empty string, scored nothing, and silently declined — for every table in
  every document (VIP-113).

  On a spreadsheet the table *is* the document, so this was the whole of it: a VNI sheet
  inside an otherwise TCVN3 workbook stayed unconverted, and `TOÅNG SOÁ` came back as
  `TONG SO`.

  Joining the cells is also what makes detection possible at that granularity. One cell
  is far too short to score — that is what the 24-character floor added in 0.1.16 is for
  — but a sheet is not.

### Measured

Over the 93 real documents in
[viparse-corpus](https://github.com/TrizenX/viparse-corpus), diacritic accuracy:

| Format | documents | 0.1.20 | 0.1.21 |
| --- | ---: | ---: | ---: |
| `.doc` | 48 | 0.972 | **0.976** |
| `.rtf` | 11 | 0.996 | 0.996 |
| `.pdf` | 5 | 0.999 | 0.999 |
| `.xls` | 28 | 0.942 | **0.979** |
| `.ppt` | 1 | 1.000 | 1.000 |
| **all** | **93** | 0.980 | **0.983** |

Word tables benefited too — this was never only a spreadsheet problem. A loader that
extracts the bytes faithfully and ignores the encoding scores **0.019** on the same set.

### One thing tried and reverted

A foreign-language block sitting inside a legacy Vietnamese document still inherits its
neighbour's encoding and is converted. Treating "content detection declined" as "this is
not Vietnamese" looked like the fix and made things worse — the corpus went from 0.980
to 0.967, because most declines are ordinary Vietnamese blocks that simply did not score
well enough to be sure.

Separating the two needs the detector to say *why* it declined, which it does not. Left
as a known limitation with a test covering the case, rather than guessed at.

## [0.1.20] — 2026-08-02

### Added

- **VNI gains `ẵ` and `Ẵ`.** 0.1.11 shipped the VNI table with `ẳ ẵ Ẳ Ẵ` deliberately
  unmapped, because no collected document contained any of them. Reading a
  mixed-encoding Lâm Đồng planning document later turned up `saün coù` (sẵn có) and
  `Ñaø Naüng` (Đà Nẵng) — two different words, one a place name that settles it, both
  invisible until the one file nobody could read got a transcript (VIP-111).

  `ẳ` and `Ẳ` remain unobserved and remain unmapped. Unmatched input still passes
  through unchanged, so a document containing them returns them unconverted rather than
  silently wrong.

### Fixed

- **Spreadsheets emitted up to 88% tabs.** openpyxl reports a worksheet's *declared*
  dimension, which routinely runs far wider than its content. On one real government
  workbook every row came back padded to 256 columns:

  | | before | after |
  | --- | ---: | ---: |
  | characters extracted | 177,515 | **29,332** |
  | of which tabs | 157,184 (88%) | 9,002 |
  | actual content | 15,566 | 15,566 |

  A hand transcript of the same file is 29,530 characters. Trimmed sheet-wide rather
  than per row, so the grid stays rectangular and a short row still lines up with the
  columns above it.

### What this does not fix

**Trimming did not move the corpus score.** The padding was output noise, not the cause
of the `.xls` diacritic figure — worth saying plainly, because the two are easy to
conflate.

The real cause is unfixed and now understood: **a spreadsheet cell is too short for
per-block content detection**, so a VNI cell inside an otherwise TCVN3 workbook stays
unconverted — `TOÅNG SOÁ` comes back as `TONG SO`. The 24-character floor that 0.1.16
needed in order not to read `MôC LôC` as VNI is the same floor a spreadsheet cell cannot
clear.

`.xls` sits at **0.942** diacritic over 28 real documents. Every other format is above
0.97.

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

[Unreleased]: https://github.com/TrizenX/viparse/compare/v0.1.29...HEAD
[0.1.29]: https://github.com/TrizenX/viparse/compare/v0.1.28...v0.1.29
[0.1.28]: https://github.com/TrizenX/viparse/compare/v0.1.27...v0.1.28
[0.1.27]: https://github.com/TrizenX/viparse/compare/v0.1.26...v0.1.27
[0.1.26]: https://github.com/TrizenX/viparse/compare/v0.1.25...v0.1.26
[0.1.25]: https://github.com/TrizenX/viparse/compare/v0.1.24...v0.1.25
[0.1.24]: https://github.com/TrizenX/viparse/compare/v0.1.23...v0.1.24
[0.1.23]: https://github.com/TrizenX/viparse/compare/v0.1.22...v0.1.23
[0.1.22]: https://github.com/TrizenX/viparse/compare/v0.1.21...v0.1.22
[0.1.21]: https://github.com/TrizenX/viparse/compare/v0.1.20...v0.1.21
[0.1.20]: https://github.com/TrizenX/viparse/compare/v0.1.19...v0.1.20
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
