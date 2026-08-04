"""OCR adapter for scans, wrapping ``pdf2image`` + ``pytesseract`` (extra ``viparse[ocr]``).

Handles a scanned **PDF** and a bare page **image** — ``.png``, ``.jpg``, ``.tif``. The
second is how a great many old Vietnamese documents actually exist: a flatbed scan saved
as archival TIFF, or a phone photograph. Until 0.1.25 those raised ``UnsupportedFormat``
at the router, before any engine saw them.

An image needs no rasterizing, so it goes straight to Pillow and never touches
``pdf2image`` or the poppler binary — which means image OCR works on a machine where only
Tesseract is installed. A multi-page TIFF is walked frame by frame, because that is what
a multi-page archival scan is.

.. warning::

   **This is the weakest path in viparse, and now there is a number for it.** Against
   rendered transcripts it reaches **0.967** diacritic accuracy on prose and **0.898** on
   degraded pages, where the conversion path scores 0.982 on the same documents. 0.967 is
   a *ceiling*: it comes from a perfect render with no skew, noise or paper texture.

   The errors land on tone marks in both directions — a hook invented on bare ``i``, the
   tone dropped from ``ề``/``ầ``/``ồ`` — which is precisely what this product exists to
   preserve. No real scanned document has been measured at all. See ``ocr/README.md`` in
   viparse-corpus.

A scanned PDF has no text layer, so the digital :class:`~viparse.engines.pdf.PdfEngine`
yields nothing. This engine rasterizes each page, converts it to grayscale, and OCRs it
with the ``vie`` model, emitting one paragraph block per page plus a low-confidence
warning. Binarization is deliberately left to Tesseract's own adaptive thresholding — a
naive global threshold can crush the faint, thin Vietnamese tone marks this product
exists to preserve (adaptive/deskew preprocessing is a future refinement). The
recognized text is already Unicode, so it carries no font signal and the engine marks it
``native_unicode`` — the moat downstream only has to enforce NFC. No Vietnamese logic
lives here.

It is **heavy** (raster + OCR) and only meaningful for scanned input, so the pipeline
runs it solely when the caller sets ``options.ocr=True`` (CLI ``--ocr``). Both Python
libraries and the underlying Tesseract/poppler binaries are required only at call time;
their absence raises a clear :class:`~viparse.errors.MissingDependency`.
"""

from __future__ import annotations

from typing import Any

from viparse.detect import CONTENT_TYPE_PDF, IMAGE_CONTENT_TYPES, detect_format
from viparse.engines._shared import blocks_to_text
from viparse.errors import ExtractionError, MissingDependency
from viparse.model import RawExtraction
from viparse.options import LoadOptions
from viparse.protocols import DEFAULT_PRIORITY, Source

_DPI = 300  # a good balance of OCR accuracy and speed for text documents
_LOW_OCR_CONFIDENCE = 60.0  # Tesseract word confidence is 0-100; below this is weak
_OCR_TIMEOUT_SECONDS = 120  # cap the Tesseract subprocess per page (untrusted-input safety)

_INSTALL_HINT = (
    "OCR needs pytesseract and the Tesseract binary; install with: "
    "pip install 'viparse[ocr]' plus the system packages tesseract-ocr tesseract-ocr-vie"
)
_PDF_INSTALL_HINT = (
    "OCR on a PDF also needs pdf2image and the poppler binary; install with: "
    "pip install 'viparse[ocr]' plus the system packages poppler-utils tesseract-ocr-vie. "
    "A page image (.png/.jpg/.tif) needs neither."
)


def _import_pytesseract() -> Any:
    """Import ``pytesseract`` lazily — the only hard requirement for OCR of an image."""
    try:
        import pytesseract
    except ImportError as exc:
        raise MissingDependency(_INSTALL_HINT) from exc
    return pytesseract


def _import_pdf2image() -> Any:
    """Import ``pdf2image`` lazily. Needed for a PDF only, and reported as such.

    Kept separate from pytesseract so that OCR of a page image does not demand poppler,
    which is the harder of the two binaries to install and irrelevant when there is
    nothing to rasterize.
    """
    try:
        import pdf2image
    except ImportError as exc:
        raise MissingDependency(_PDF_INSTALL_HINT) from exc
    return pdf2image


class OcrEngine:
    """OCRs a scanned ``.pdf`` into one text block per page, with a confidence signal."""

    #: Below the digital PDF engine's baseline — though selection is really governed by
    #: :meth:`Pipeline._select_by_ocr`, which runs OCR only when ``options.ocr`` is True.
    priority = DEFAULT_PRIORITY - 10
    #: Dependency + extra + external binary reported by ``viparse doctor``.
    dependency = "pytesseract"
    extra = "ocr"
    binary = "tesseract"
    #: Marks this as an OCR engine; the pipeline only selects it when ``options.ocr`` is True.
    ocr = True

    def supports(self, content_type: str) -> bool:
        return content_type == CONTENT_TYPE_PDF or content_type in IMAGE_CONTENT_TYPES

    def extract(self, source: Source, options: LoadOptions) -> RawExtraction:
        pytesseract = _import_pytesseract()
        # Re-detected rather than passed in: this engine now answers to several content
        # types, and the result must say which one it actually read.
        content_type = detect_format(source).content_type
        is_image = content_type in IMAGE_CONTENT_TYPES

        # Poppler is only ever missing on the PDF path, and the two binaries are named
        # separately so the error tells the caller which one to go and install.
        poppler_missing: tuple[type[BaseException], ...] = ()
        pdf2image = None
        if not is_image:
            pdf2image = _import_pdf2image()
            poppler_missing = (pdf2image.exceptions.PDFInfoNotInstalledError,)

        try:
            images = (
                _image_pages(source)
                if is_image
                else pdf2image.convert_from_path(str(source), dpi=_DPI)  # type: ignore[union-attr]
            )
            pages = [_ocr_page(pytesseract, image) for image in images]
        except poppler_missing as exc:
            raise MissingDependency(_PDF_INSTALL_HINT) from exc
        except pytesseract.TesseractNotFoundError as exc:
            raise MissingDependency(_INSTALL_HINT) from exc
        except OSError as exc:  # Pillow raises OSError on a truncated or unreadable image
            raise ExtractionError(f"could not read image {source!s}: {exc}") from exc
        except RuntimeError as exc:  # pytesseract raises RuntimeError on timeout / Tesseract error
            raise ExtractionError(f"OCR failed or timed out: {exc}") from exc

        blocks: list[dict[str, Any]] = []
        weak_pages = 0
        for text, confidence in pages:
            if not text:
                continue
            blocks.append({"type": "paragraph", "text": text})
            if confidence < _LOW_OCR_CONFIDENCE:
                weak_pages += 1
        warnings: list[str] = []
        if weak_pages:
            warnings.append(
                f"{weak_pages} page(s) OCR'd below {_LOW_OCR_CONFIDENCE:.0f}% confidence; "
                "the text may contain recognition errors"
            )
        return RawExtraction(
            source=str(source),
            content_type=content_type,
            text=blocks_to_text(blocks),
            engine="ocr",
            # OCR output is Unicode with no font: no legacy-encoding question, so mark it
            # so the normalizer does not emit a spurious low-confidence encoding warning.
            signals={"fonts": [], "blocks": blocks, "native_unicode": True},
            warnings=warnings,
        )


def _image_pages(source: Source) -> list[Any]:
    """Every frame of a page image, as Pillow images.

    A multi-page TIFF is one file holding many scanned pages, which is exactly what a
    digitised archive looks like; reading only the first would drop the rest in silence —
    the failure mode this project keeps running into. Each frame is copied out of the
    sequence because Pillow frames are views over one open file handle, and the file is
    closed before OCR runs.
    """
    from PIL import Image, ImageSequence

    with Image.open(str(source)) as image:
        return [frame.copy() for frame in ImageSequence.Iterator(image)]


def _ocr_page(pytesseract: Any, image: Any) -> tuple[str, float]:
    """OCR one page image (grayscale), returning its text and mean word confidence."""
    data = pytesseract.image_to_data(
        image.convert("L"),
        lang="vie",
        timeout=_OCR_TIMEOUT_SECONDS,
        output_type=pytesseract.Output.DICT,
    )
    words: list[str] = []
    confidences: list[float] = []
    for word, raw_conf in zip(data["text"], data["conf"], strict=True):
        conf = float(raw_conf)
        if conf < 0:  # Tesseract marks non-text regions with conf == -1
            continue
        confidences.append(conf)
        if word.strip():
            words.append(word)
    text = " ".join(words)
    confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return text, confidence
