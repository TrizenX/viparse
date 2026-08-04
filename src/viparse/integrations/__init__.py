"""Adapters that map a viparse :class:`~viparse.model.Document` onto RAG-framework types.

Each framework gets two entry points: a **converter** for text you already loaded with
viparse, and a **loader/reader** class in the shape that framework's pipelines are written
around. The second matters more than it looks — a converter is only ever reached by
someone who already went looking for viparse.

Each adapter lazily imports its framework, so importing this package pulls in neither
LangChain nor LlamaIndex — install ``viparse[langchain]`` / ``viparse[llamaindex]`` to use one.
"""

from __future__ import annotations

from typing import Any

from viparse.integrations.langchain import to_langchain_documents
from viparse.integrations.llamaindex import to_llamaindex_documents

__all__ = [
    "ViparseReader",
    "VietnameseDocumentLoader",
    "to_langchain_documents",
    "to_llamaindex_documents",
]


def __getattr__(name: str) -> Any:
    """Forward the class names to their modules, still without importing a framework."""
    if name == "VietnameseDocumentLoader":
        from viparse.integrations import langchain

        return langchain.VietnameseDocumentLoader
    if name == "ViparseReader":
        from viparse.integrations import llamaindex

        return llamaindex.ViparseReader
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
