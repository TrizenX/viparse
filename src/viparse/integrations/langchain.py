"""LangChain integration: a document loader, and the converter underneath it.

Two entry points, for two different callers.

:func:`to_langchain_documents` converts a viparse :class:`~viparse.model.Document` that
you already have. It only helps someone who has already chosen viparse.

:class:`VietnameseDocumentLoader` is a ``BaseLoader``, which is the shape a LangChain
pipeline is actually written around::

    loader = VietnameseDocumentLoader("bao_cao_cu.doc")
    docs = loader.load()

That distinction is the whole point of this class existing. A converter is reached by
someone who went looking for viparse; a loader is reached by someone who was already
writing a LangChain pipeline and needed a Vietnamese document read correctly. The second
is the only one of the two that can be *found*.

LangChain is an optional, lazily-imported dependency (``viparse[langchain]``); importing
this module never imports LangChain, so ``core`` stays light.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from viparse.errors import MissingDependency
from viparse.integrations._common import document_records
from viparse.model import Document


def to_langchain_documents(document: Document) -> list[Any]:
    """Convert ``document`` to a list of LangChain ``Document`` objects.

    Emits one LangChain ``Document`` per viparse chunk when the document is chunked, else a
    single one for the whole document. The viparse text maps to ``page_content`` and the
    flattened provenance to ``metadata``. Raises :class:`~viparse.errors.MissingDependency`
    if LangChain is not installed.
    """
    lc_document = _langchain_document_class()
    return [
        lc_document(page_content=text, metadata=metadata)
        for text, metadata in document_records(document)
    ]


def _langchain_document_class() -> Any:
    try:
        from langchain_core.documents import Document as LangChainDocument
    except ImportError as exc:
        raise MissingDependency(
            "LangChain is required for this integration; install viparse[langchain]"
        ) from exc
    return LangChainDocument


def _base_loader_class() -> Any:
    """Import ``BaseLoader`` lazily, raising a clear error if LangChain is missing."""
    try:
        from langchain_core.document_loaders import BaseLoader
    except ImportError as exc:
        raise MissingDependency(
            "LangChain is required for VietnameseDocumentLoader; install it with: "
            "pip install 'viparse[langchain]'"
        ) from exc
    return BaseLoader


def _make_loader() -> Any:
    """Build the loader class against the installed LangChain.

    Defined here rather than at module scope because the base class cannot be imported
    until LangChain is known to be present, and importing this module must not require it.
    """
    base = _base_loader_class()

    class VietnameseDocumentLoader(base):  # type: ignore[misc, valid-type]
        """Load a Vietnamese document — legacy encodings included — into LangChain.

        Accepts the same options as :func:`viparse.load`, so ``encoding``, ``ocr``,
        ``output`` and ``chunk`` behave identically. ``chunk`` is worth setting: with it,
        one LangChain ``Document`` is emitted per chunk with its section carried in
        ``metadata``, which is what a retriever wants.
        """

        def __init__(self, file_path: str, **options: Any) -> None:
            self.file_path = file_path
            self.options = options

        def lazy_load(self) -> Iterator[Any]:
            """Yield one LangChain ``Document`` per viparse chunk.

            ``lazy_load`` rather than ``load``: the base class implements ``load`` in
            terms of this one, so overriding it here gives both, and a caller streaming a
            large document is not forced to materialise every chunk first.
            """
            from viparse import load

            for document in load(self.file_path, **self.options):
                yield from to_langchain_documents(document)

    return VietnameseDocumentLoader


def __getattr__(name: str) -> Any:
    """Expose ``VietnameseDocumentLoader`` without importing LangChain at module import.

    A module-level ``__getattr__`` keeps the class importable by name — the way a caller
    expects to write it — while the framework is still only imported on first use.
    """
    if name == "VietnameseDocumentLoader":
        return _make_loader()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
