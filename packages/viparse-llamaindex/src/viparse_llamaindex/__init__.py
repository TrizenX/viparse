"""LlamaIndex integration for viparse, as a package a LlamaIndex user can find.

The code lives in ``viparse.integrations.llamaindex`` and is installed by
``pip install "viparse[llamaindex]"``. This distribution adds nothing to it and
deliberately so — it exists to be **discoverable**, not to be different.

Why a second name for one thing
-------------------------------
LlamaIndex no longer accepts third-party integrations into its own repository:

    "we are no longer accepting new integration packages in this repository… PRs that add
    a new `pyproject.toml` will be automatically closed."

So the only way to appear where a LlamaIndex user looks is to be a package on PyPI that
says LlamaIndex in its name and its description. That is the whole job of this file.

Why not ``llama-index-readers-viparse``
---------------------------------------
That prefix is LlamaHub's own reader namespace. Naming a package into someone else's
namespace implies it is listed there, and it is not — the registry that convention refers
to stopped taking submissions. ``viparse-llamaindex`` claims nothing it cannot back, and
matches its LangChain sibling.

There is no version lock-step. This package pins ``viparse[llamaindex]`` by lower bound
and should almost never need releasing again — if it does, the reader's signature changed,
which is a thing worth noticing.
"""

from __future__ import annotations

from viparse.integrations import ViparseReader, to_llamaindex_documents

__all__ = ["ViparseReader", "to_llamaindex_documents"]

__version__ = "0.1.0"
