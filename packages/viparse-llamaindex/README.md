# viparse-llamaindex

**LlamaIndex integration for [viparse](https://github.com/TrizenX/viparse)** — read Vietnamese
documents, including files written in the pre-Unicode **TCVN3 / VNI / VISCII / VPS**
encodings that generic loaders return as `B¸o c¸o tµi chÝnh`.

```bash
pip install viparse-llamaindex
```

```python
from viparse_llamaindex import ViparseReader

documents = ViparseReader().load_data("bao_cao_cu.doc")
```

Takes the same options as `viparse.load()` — `encoding`, `ocr`, `output`, `chunk` —
and streams rather than materialising a whole document first.

## What it is

A thin, deliberately empty package. The code lives in `viparse.integrations` and ships
with `pip install "viparse[llamaindex]"`; this distribution exists so that a LlamaIndex user
can **find** it, because LlamaIndex no longer accepts third-party integrations into its own
repositories.

## Why not `llama-index-readers-viparse`

That prefix belongs to LlamaIndex's own packages. Using it would imply an official
integration that does not exist, and a PyPI name cannot be given back.

## Accuracy

**0.986** diacritic accuracy over 96 hand-transcribed Vietnamese government documents,
against **0.019** for the same reader with conversion switched off — same documents, same
published command, one flag apart. The corpus, the metric and every raw result are
[public](https://github.com/TrizenX/viparse-corpus), including a written account of the
ways the number is weaker than it looks.

MIT © 2026 Đinh Minh Trí (Kayden)
