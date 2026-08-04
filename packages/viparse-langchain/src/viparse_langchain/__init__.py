"""LangChain integration for viparse, as a package a LangChain user can find.

The code lives in ``viparse.integrations.langchain`` and is installed by
``pip install "viparse[langchain]"``. This distribution adds nothing to it and
deliberately so — it exists to be **discoverable**, not to be different.

Why a second name for one thing
-------------------------------
LangChain no longer accepts third-party integrations into its own repositories:

    "New integrations are not accepted as PRs to `langchain-ai` repos — they must be
    published independently to PyPI or npm."

So the only way to appear where a LangChain user looks is to be a package on PyPI that
says LangChain in its name and its description. That is the whole job of this file.

Why not ``langchain-viparse``
-----------------------------
Every ``langchain-*`` distribution on PyPI is published by ``langchain-ai`` itself —
``langchain-openai``, ``langchain-qdrant``, ``langchain-unstructured``. Taking that prefix
as an unaffiliated project would read as an official partnership that does not exist, and
a PyPI name cannot be given back. ``viparse-langchain`` says what this actually is: the
LangChain half of viparse.

There is no version lock-step. This package pins ``viparse[langchain]`` by lower bound and
should almost never need releasing again — if it does, the loader's signature changed,
which is a thing worth noticing.
"""

from __future__ import annotations

from viparse.integrations import VietnameseDocumentLoader, to_langchain_documents

__all__ = ["VietnameseDocumentLoader", "to_langchain_documents"]

__version__ = "0.1.0"
