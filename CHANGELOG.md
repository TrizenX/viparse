# Changelog

All notable changes to viparse are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/TrizenX/viparse/compare/v0.1.8...HEAD
[0.1.8]: https://github.com/TrizenX/viparse/compare/v0.1.7...v0.1.8
[0.1.7]: https://github.com/TrizenX/viparse/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/TrizenX/viparse/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/TrizenX/viparse/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/TrizenX/viparse/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/TrizenX/viparse/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/TrizenX/viparse/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/TrizenX/viparse/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/TrizenX/viparse/releases/tag/v0.1.0
