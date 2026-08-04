"""LlamaIndex integration: a reader, and the converter underneath it.

:func:`to_llamaindex_documents` converts a viparse :class:`~viparse.model.Document` you
already have. :class:`ViparseReader` is a ``BaseReader``, which is the shape a LlamaIndex
pipeline is written around::

    documents = ViparseReader().load_data("bao_cao_cu.doc")

The converter is reached by someone who already chose viparse; the reader is reached by
someone who was already writing a LlamaIndex pipeline and needed a Vietnamese document
read correctly. Only the second can be found by a stranger.

LlamaIndex is an optional, lazily-imported dependency (``viparse[llamaindex]``); importing
this module never imports LlamaIndex, so ``core`` stays light.
"""

from __future__ import annotations

from typing import Any

from viparse.errors import MissingDependency
from viparse.integrations._common import document_records
from viparse.model import Document


def to_llamaindex_documents(document: Document) -> list[Any]:
    """Convert ``document`` to a list of LlamaIndex ``Document`` objects.

    Emits one LlamaIndex ``Document`` per viparse chunk when the document is chunked, else a
    single one for the whole document. The viparse text maps to ``text`` and the flattened
    provenance to ``metadata``. Raises :class:`~viparse.errors.MissingDependency` if
    LlamaIndex is not installed.
    """
    li_document = _llamaindex_document_class()
    return [
        li_document(text=text, metadata=metadata) for text, metadata in document_records(document)
    ]


def _llamaindex_document_class() -> Any:
    try:
        from llama_index.core.schema import Document as LlamaIndexDocument
    except ImportError as exc:
        raise MissingDependency(
            "LlamaIndex is required for this integration; install viparse[llamaindex]"
        ) from exc
    return LlamaIndexDocument


def _base_reader_class() -> Any:
    """Import ``BaseReader`` lazily, raising a clear error if LlamaIndex is missing."""
    try:
        from llama_index.core.readers.base import BaseReader
    except ImportError as exc:
        raise MissingDependency(
            "LlamaIndex is required for ViparseReader; install it with: "
            "pip install 'viparse[llamaindex]'"
        ) from exc
    return BaseReader


def _make_reader() -> Any:
    """Build the reader class against the installed LlamaIndex."""
    base = _base_reader_class()

    class ViparseReader(base):  # type: ignore[misc, valid-type]
        """Read a Vietnamese document — legacy encodings included — into LlamaIndex.

        Accepts the same options as :func:`viparse.load`. Options given to the constructor
        are defaults; options given to :meth:`load_data` override them for that call, so
        one reader can serve a directory of mixed formats.
        """

        def __init__(self, **options: Any) -> None:
            super().__init__()
            self._options = options

        def load_data(self, file: Any, **options: Any) -> list[Any]:
            """Load ``file`` into a list of LlamaIndex ``Document`` objects."""
            from viparse import load

            merged = {**self._options, **options}
            documents = load(str(file), **merged)
            return [item for document in documents for item in to_llamaindex_documents(document)]

    return ViparseReader


def __getattr__(name: str) -> Any:
    """Expose ``ViparseReader`` without importing LlamaIndex at module import."""
    if name == "ViparseReader":
        return _make_reader()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
