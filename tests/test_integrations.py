"""Tests for the LangChain / LlamaIndex adapters (SPEC-4 E4.4).

The frameworks are optional deps viparse does not pull into CI, so each is stubbed with a
minimal fake module (the same injection pattern the OCR / LibreOffice engine tests use),
giving deterministic coverage of the mapping without the heavy dependency.
"""

from __future__ import annotations

import sys
import types
from collections.abc import Iterator

import pytest

from viparse.errors import MissingDependency
from viparse.integrations import to_langchain_documents, to_llamaindex_documents
from viparse.model import Chunk, Document, DocumentMetadata


class _FakeLangChainDocument:
    def __init__(self, page_content: str, metadata: dict[str, object]) -> None:
        self.page_content = page_content
        self.metadata = metadata


class _FakeLlamaIndexDocument:
    def __init__(self, text: str, metadata: dict[str, object]) -> None:
        self.text = text
        self.metadata = metadata


@pytest.fixture
def fake_langchain(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    package = types.ModuleType("langchain_core")
    documents = types.ModuleType("langchain_core.documents")
    documents.Document = _FakeLangChainDocument  # type: ignore[attr-defined]
    loaders = types.ModuleType("langchain_core.document_loaders")

    class _FakeBaseLoader:
        """Enough of BaseLoader to exercise ours: `load` defined via `lazy_load`."""

        def load(self) -> list[object]:
            return list(self.lazy_load())  # type: ignore[attr-defined]

    loaders.BaseLoader = _FakeBaseLoader  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "langchain_core", package)
    monkeypatch.setitem(sys.modules, "langchain_core.documents", documents)
    monkeypatch.setitem(sys.modules, "langchain_core.document_loaders", loaders)
    yield


@pytest.fixture
def fake_llamaindex(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    package = types.ModuleType("llama_index")
    core = types.ModuleType("llama_index.core")
    schema = types.ModuleType("llama_index.core.schema")
    schema.Document = _FakeLlamaIndexDocument  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "llama_index", package)
    monkeypatch.setitem(sys.modules, "llama_index.core", core)
    readers = types.ModuleType("llama_index.core.readers")
    base_mod = types.ModuleType("llama_index.core.readers.base")

    class _FakeBaseReader:
        pass

    base_mod.BaseReader = _FakeBaseReader  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "llama_index.core.schema", schema)
    monkeypatch.setitem(sys.modules, "llama_index.core.readers", readers)
    monkeypatch.setitem(sys.modules, "llama_index.core.readers.base", base_mod)
    yield


def _document(
    *,
    chunks: list[Chunk] | None = None,
    warnings: list[str] | None = None,
    extra: dict[str, object] | None = None,
) -> Document:
    metadata = DocumentMetadata(
        source="a.docx",
        content_type="application/vnd.docx",
        page=2,
        sheet="S1",
        engine="docx",
        warnings=warnings or [],
        extra=extra or {},
    )
    return Document(text="full text", metadata=metadata, chunks=chunks or [])


_CHUNKS = [
    Chunk(text="chunk zero", metadata={"section": "Intro", "page": 2, "sheet": "S1"}, index=0),
    Chunk(text="chunk one", metadata={"section": "Body", "page": 2, "sheet": "S1"}, index=1),
]


# --- LangChain -------------------------------------------------------------------------


def test_langchain_unchunked_yields_one_document(fake_langchain: None) -> None:
    (doc,) = to_langchain_documents(_document())
    assert isinstance(doc, _FakeLangChainDocument)
    assert doc.page_content == "full text"
    assert doc.metadata["source"] == "a.docx"
    assert doc.metadata["page"] == 2
    assert doc.metadata["engine"] == "docx"
    assert "chunk_index" not in doc.metadata  # not chunked
    assert "warnings" not in doc.metadata  # empty warnings are omitted


def test_langchain_chunked_yields_one_document_per_chunk(fake_langchain: None) -> None:
    docs = to_langchain_documents(_document(chunks=_CHUNKS))
    assert [d.page_content for d in docs] == ["chunk zero", "chunk one"]
    assert [d.metadata["chunk_index"] for d in docs] == [0, 1]
    assert docs[0].metadata["section"] == "Intro"
    assert docs[0].metadata["source"] == "a.docx"  # document provenance rides on each chunk


def test_langchain_flattens_warnings_and_extra(fake_langchain: None) -> None:
    (doc,) = to_langchain_documents(_document(warnings=["page 3 failed"], extra={"custom": "v"}))
    assert doc.metadata["warnings"] == ["page 3 failed"]
    assert doc.metadata["custom"] == "v"


def test_langchain_chunk_metadata_is_independent(fake_langchain: None) -> None:
    # Nested mutables (the warnings list) must be copied per chunk, so mutating one chunk's
    # metadata never bleeds into a sibling chunk or the source document.
    document = _document(chunks=_CHUNKS, warnings=["shared"])
    docs = to_langchain_documents(document)
    docs[0].metadata["warnings"].append("only chunk 0")
    assert docs[1].metadata["warnings"] == ["shared"]
    assert document.metadata.warnings == ["shared"]


def test_langchain_missing_dependency_names_the_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    # Null the exact submodule the adapter imports (not just the parent) so a cached real
    # install can't short-circuit the import and mask the MissingDependency path.
    monkeypatch.setitem(sys.modules, "langchain_core", None)
    monkeypatch.setitem(sys.modules, "langchain_core.documents", None)
    with pytest.raises(MissingDependency, match=r"viparse\[langchain\]"):
        to_langchain_documents(_document())


# --- LlamaIndex ------------------------------------------------------------------------


def test_llamaindex_unchunked_yields_one_document(fake_llamaindex: None) -> None:
    (doc,) = to_llamaindex_documents(_document())
    assert isinstance(doc, _FakeLlamaIndexDocument)
    assert doc.text == "full text"
    assert doc.metadata["source"] == "a.docx"


def test_llamaindex_chunked_yields_one_document_per_chunk(fake_llamaindex: None) -> None:
    docs = to_llamaindex_documents(_document(chunks=_CHUNKS))
    assert [d.text for d in docs] == ["chunk zero", "chunk one"]
    assert [d.metadata["chunk_index"] for d in docs] == [0, 1]
    assert docs[1].metadata["section"] == "Body"


def test_llamaindex_missing_dependency_names_the_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "llama_index", None)
    monkeypatch.setitem(sys.modules, "llama_index.core.schema", None)  # exact imported submodule
    with pytest.raises(MissingDependency, match=r"viparse\[llamaindex\]"):
        to_llamaindex_documents(_document())


# --- Loader / reader classes -------------------------------------------------
#
# These matter more than the converters they wrap. A converter is only ever reached by
# someone who already chose viparse; a loader is reached by someone who was already
# writing a LangChain pipeline and needed a Vietnamese document read correctly.


def _tcvn3_docx(path) -> str:  # noqa: ANN001
    """A real .docx whose text is TCVN3 in a .VnTime run — the case the loader exists for.

    Built with python-docx rather than by hand: a bare `word/document.xml` in a zip has no
    `[Content_Types].xml` and every OOXML reader rejects it.
    """
    docx = pytest.importorskip("docx")
    document = docx.Document()
    run = document.add_paragraph().add_run("B\u00b8o c\u00b8o t\u00b5i ch\u00ddnh")
    run.font.name = ".VnTime"
    document.save(str(path))
    return str(path)


@pytest.mark.usefixtures("fake_langchain")
def test_langchain_loader_reads_a_file_end_to_end(tmp_path) -> None:  # noqa: ANN001
    from viparse.integrations import VietnameseDocumentLoader

    source = _tcvn3_docx(tmp_path / "a.docx")
    docs = VietnameseDocumentLoader(source).load()
    assert [d.page_content for d in docs] == ["B\u00e1o c\u00e1o t\u00e0i ch\u00ednh"]
    assert docs[0].metadata["encoding_detected"] == "tcvn3"


@pytest.mark.usefixtures("fake_langchain")
def test_langchain_loader_forwards_load_options(tmp_path) -> None:  # noqa: ANN001
    """Options reach viparse.load, so the loader is not a lossy wrapper.

    `encoding="none"` is the clearest probe: it must come back unconverted.
    """
    from viparse.integrations import VietnameseDocumentLoader

    source = _tcvn3_docx(tmp_path / "a.docx")
    docs = VietnameseDocumentLoader(source, encoding="none").load()
    assert docs[0].page_content == "B\u00b8o c\u00b8o t\u00b5i ch\u00ddnh"


@pytest.mark.usefixtures("fake_langchain")
def test_langchain_loader_is_lazy(tmp_path) -> None:  # noqa: ANN001
    # lazy_load must be a generator: the base class builds `load` on top of it, and a
    # caller streaming a large document should not have to materialise it first.
    from viparse.integrations import VietnameseDocumentLoader

    stream = VietnameseDocumentLoader(_tcvn3_docx(tmp_path / "a.docx")).lazy_load()
    assert isinstance(stream, Iterator)


@pytest.mark.usefixtures("fake_llamaindex")
def test_llamaindex_reader_reads_a_file_end_to_end(tmp_path) -> None:  # noqa: ANN001
    from viparse.integrations import ViparseReader

    docs = ViparseReader().load_data(_tcvn3_docx(tmp_path / "a.docx"))
    assert [d.text for d in docs] == ["B\u00e1o c\u00e1o t\u00e0i ch\u00ednh"]


@pytest.mark.usefixtures("fake_llamaindex")
def test_llamaindex_reader_call_options_override_constructor_options(tmp_path) -> None:  # noqa: ANN001
    from viparse.integrations import ViparseReader

    reader = ViparseReader(encoding="none")
    docs = reader.load_data(_tcvn3_docx(tmp_path / "a.docx"), encoding="tcvn3")
    assert docs[0].text == "B\u00e1o c\u00e1o t\u00e0i ch\u00ednh"


def test_loader_without_langchain_raises_missing_dependency(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setitem(sys.modules, "langchain_core.document_loaders", None)
    with pytest.raises(MissingDependency, match=r"viparse\[langchain\]"):
        from viparse.integrations import VietnameseDocumentLoader  # noqa: F401


def test_reader_without_llamaindex_raises_missing_dependency(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setitem(sys.modules, "llama_index.core.readers.base", None)
    with pytest.raises(MissingDependency, match=r"viparse\[llamaindex\]"):
        from viparse.integrations import ViparseReader  # noqa: F401
