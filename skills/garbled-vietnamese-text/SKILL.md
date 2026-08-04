---
name: garbled-vietnamese-text
description: Use when Vietnamese text has come out wrong — `B¸o c¸o tµi chÝnh` instead of `Báo cáo tài chính`, `Coäng hoøa xaõ hoäi` instead of `Cộng hòa xã hội`, `QuyÕt ®Þnh` instead of `Quyết định` — or when a Word/PDF file mentions fonts named `.VnTime`, `.VnTimeH` or `VNI-Times`. Covers the pre-Unicode Vietnamese encodings TCVN3, VNI, VISCII and VPS, and how to convert them back.
---

# Vietnamese text that came out wrong

## Recognise it first

You are looking at this if Vietnamese text has ASCII words that read correctly but
diacritics replaced by unrelated Latin-1 characters:

| what you see | what it says |
| --- | --- |
| `B¸o c¸o tµi chÝnh` | Báo cáo tài chính |
| `QuyÕt ®Þnh cña Bé tr­ëng` | Quyết định của Bộ trưởng |
| `Coäng hoøa xaõ hoäi chuû nghóa` | Cộng hòa xã hội chủ nghĩa |
| `Ñoäc laäp - Töï do - Haïnh phuùc` | Độc lập - Tự do - Hạnh phúc |

**Nothing is lost and nothing is corrupt.** This is a pre-Unicode Vietnamese encoding
being read as Latin-1. It converts back exactly.

Do not try to guess the text from context, and do not "fix" it by rewriting the
Vietnamese yourself. The bytes are a faithful record; a conversion is reversible and a
guess is not.

## Which encoding

Two families cover almost everything, and they look different at a glance:

**TCVN3** replaces the vowel with one high byte, so words get *shorter*: `lËp` is lập,
`§éc` is Độc. Fonts are named `.VnTime`, `.VnTimeH`. This is what Vietnamese government
and university documents from roughly 1995–2008 use.

**VNI** keeps the ASCII vowel and appends a mark, so words get *longer*: `laäp` is lập,
`Ñoäc` is Độc. Font is `VNI-Times`. More common in southern Vietnam and in overseas
Vietnamese publishing.

**VISCII** and **VPS** exist but are rare in documents — they were charsets for email,
Usenet and early web pages, declared as `charset=VISCII`, not font tricks. If you see a
`charset` declaration naming one, that is your answer.

You do not have to decide. The tools below detect it.

## Fixing it

### If text is already in your context

This is the common case — some other tool handed you the broken text and there is no
file to point at.

With the MCP server (`pip install "viparse[mcp]"`), call
`repair_garbled_vietnamese` with the text. Otherwise:

```python
import viparse

print(viparse.fix("B¸o c¸o tµi chÝnh"))
# Báo cáo tài chính

viparse.detect_text_encoding("B¸o c¸o tµi chÝnh")  # 'tcvn3', or None
```

`viparse.fix` takes text, not a path, so it works on whatever another tool handed you.

### If you have the file

```bash
pip install "viparse[office]"
viparse path/to/file.doc
```

```python
import viparse

docs = viparse.load("file.doc", output="text")
```

Legacy `.doc` needs LibreOffice installed; `.docx`, `.pdf`, `.rtf` and `.xlsx` do not.

## Things that will bite you

**Do not convert text that is already Unicode.** Running a legacy table over correct
Vietnamese destroys it. Every tool here passes Unicode through unchanged — keep that
property if you write your own.

**A font name is not proof.** A `.VnTime` declaration survives conversion, so a document
migrated to Unicode often still names the legacy font. Screening 62 files on the font
alone put 27 already-Unicode documents in the set. Decide from the text, not the font
table.

**One document can be two encodings.** Files assembled from sections typed on different
machines carry both, sometimes with a font name that is wrong for most of the file. Pass
`encoding="auto"` so detection runs per block rather than once for the document.

**Give detection a phrase, not a word.** It scores character frequencies, and a
four-character fragment has nothing to score. `laäp` alone is detected as VISCII and
comes back `laảp`; `Ñoäc laäp` is detected as VNI and comes back `Độc lập`. If a
fragment is genuinely all you have, name the encoding — `encoding="vni"` converts `laäp`
to `lập` correctly.

**Non-Vietnamese text can look legacy.** Spanish `señor` scores as Vietnamese to a
frequency detector and comes back as `seđor`. Only assert `encoding="auto"` when you
know the source is Vietnamese.

**Uppercase headings may come back lowercase.** TCVN3 has no uppercase accented letters
— an uppercase heading is typed with the same bytes as lowercase and drawn uppercase by
`.VnTimeH`. Byte-level conversion cannot always recover the case, so `TOÀN` may return
as `TOàN`. Fix it by reading, not by uppercasing everything.

## Where the claims here come from

Accuracy figures and the documents behind them:
<https://github.com/TrizenX/viparse-corpus> — 48 Vietnamese government documents from
2001–2009, hand-transcribed, with the metric and the raw results published, including
the ways the numbers are weaker than they look.

A loader that extracts the bytes faithfully and ignores the encoding scores **0.014** on
diacritics over that corpus. The text looks 79% intact and carries 1.4% of the
Vietnamese, which is why this is worth handling rather than eyeballing.
