"""Survey a directory: which files carry a legacy encoding, and which need OCR.

The question this answers is not "convert my files". It is the one that comes before
that, and the one nobody currently has a way to ask: **do I even have this problem?**

Today the answer costs an install, a script, and knowing to print the first two hundred
characters and look at them. That is a lot to ask of someone who does not yet believe
anything is wrong — and someone who does not believe anything is wrong is the entire
audience, because the failure this library exists for does not raise, does not return
empty, and does not shorten the text. It looks like it worked.

A scan turns that into one command and, more importantly, into **the reader's own
number**. "47 of your 312 files" is an argument; "0.019 diacritic accuracy on our corpus"
is a claim about us.

What it does not do
-------------------
It does not convert anything and it does not write anything. A tool whose job is to tell
you the truth about your files should not also be modifying them.

It reports what the normalizer *would* decide, by running the real detection path rather
than a cheaper approximation of it — a survey that disagrees with the converter is worse
than no survey, because it would send someone to look for a bug that is in the survey.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from viparse.detect import IMAGE_CONTENT_TYPES, detect_format
from viparse.errors import ViparseError

#: Content types that only OCR can read, so "needs OCR" is a property of the file rather
#: than a guess about it.
_OCR_ONLY = IMAGE_CONTENT_TYPES


@dataclass(frozen=True, slots=True)
class FileReport:
    """One file's verdict."""

    path: Path
    #: Legacy encoding the normalizer settled on, or ``None`` if the text was already
    #: Unicode — or if nothing could be read.
    encoding: str | None = None
    #: True when the file can only be read by OCR (a page image, or a PDF with no text).
    needs_ocr: bool = False
    #: Populated when the file could not be read at all; the file is then counted as
    #: unreadable rather than silently as clean.
    error: str | None = None


@dataclass(slots=True)
class ScanReport:
    """What a scan found, in the shape the summary is printed from."""

    files: list[FileReport] = field(default_factory=list)

    @property
    def legacy(self) -> list[FileReport]:
        return [f for f in self.files if f.encoding]

    @property
    def needs_ocr(self) -> list[FileReport]:
        return [f for f in self.files if f.needs_ocr and not f.error]

    @property
    def unreadable(self) -> list[FileReport]:
        return [f for f in self.files if f.error]

    @property
    def clean(self) -> list[FileReport]:
        return [f for f in self.files if not (f.encoding or f.needs_ocr or f.error)]

    @property
    def encodings(self) -> Counter[str]:
        return Counter(f.encoding for f in self.legacy if f.encoding)


def scan_file(path: Path) -> FileReport:
    """Decide what one file is, without converting or writing anything.

    ``encoding="auto"`` is passed deliberately. Content detection is opt-in for
    :func:`viparse.load` because a caller handing over a file may not know what is in it;
    here, finding out what is in it *is* the request.
    """
    from viparse import load

    try:
        detected = detect_format(path)
    except ViparseError as exc:
        return FileReport(path, error=type(exc).__name__)

    needs_ocr = detected.content_type in _OCR_ONLY
    try:
        documents = load(str(path), encoding="auto")
    except ViparseError as exc:
        # A file that cannot be read is reported as such. Counting it as clean would be
        # the one dishonest outcome available here.
        return FileReport(path, needs_ocr=needs_ocr, error=type(exc).__name__)

    encoding = documents[0].metadata.encoding_detected if documents else None
    # A PDF with no text layer reads as empty rather than failing, and empty is exactly
    # what a scanned page looks like from here.
    if not needs_ocr and documents and not documents[0].text.strip():
        needs_ocr = True
    return FileReport(path, encoding=encoding, needs_ocr=needs_ocr)


def scan(paths: list[Path]) -> ScanReport:
    """Scan every file in ``paths``."""
    return ScanReport(files=[scan_file(path) for path in paths])


def format_report(report: ScanReport, *, show_files: int = 0) -> str:
    """Render a scan as the paragraph someone pastes into a chat to explain the problem.

    Ordered so the number that matters is not last: how many files are affected, then what
    that means for them, then the detail. A reader who stops after two lines should still
    have the finding.
    """
    total = len(report.files)
    if not total:
        return "no files matched"

    legacy, ocr = report.legacy, report.needs_ocr
    lines = [f"{total} file(s)"]

    if legacy:
        breakdown = " · ".join(f"{name} {count}" for name, count in report.encodings.most_common())
        lines.append(f"  {len(legacy):>4}  legacy encoding   {breakdown}")
    if ocr:
        lines.append(f"  {len(ocr):>4}  needs OCR         no text layer; install viparse[ocr]")
    if report.unreadable:
        kinds = Counter(f.error for f in report.unreadable)
        detail = " · ".join(f"{k} {v}" for k, v in kinds.most_common())
        lines.append(f"  {len(report.unreadable):>4}  unreadable        {detail}")
    lines.append(f"  {len(report.clean):>4}  already Unicode")

    if legacy:
        lines += [
            "",
            f"Those {len(legacy)} file(s) reach a vector database as mojibake — "
            "`B¸o c¸o tµi chÝnh` rather than `Báo cáo tài chính`.",
            "Nothing errors and nothing is empty, so this does not show up in a log.",
        ]
        if show_files:
            lines.append("")
            for item in legacy[:show_files]:
                lines.append(f"  {item.encoding:<8} {item.path}")
            if len(legacy) > show_files:
                # Never a silent truncation: a list that stops without saying so reads as
                # the whole list.
                lines.append(f"  … and {len(legacy) - show_files} more (--list to widen)")
    elif not ocr:
        lines += ["", "No legacy encodings found. Nothing here needs viparse."]

    return "\n".join(lines)
