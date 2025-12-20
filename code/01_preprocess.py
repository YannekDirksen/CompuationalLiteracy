#!/usr/bin/env python3
"""
01_preprocess.py

Preprocess Grimm's Fairy Tales corpus:
- sentence segmentation
- tokenization
- lemmatization
- POS tagging + dependency parsing

Outputs:
- results/sentences.csv
- results/tokens.csv
"""

from __future__ import annotations

import csv
import os
from pathlib import Path
import sys

import spacy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "grimms.txt"
RESULTS_DIR = PROJECT_ROOT / "results"
SENTENCES_OUT = RESULTS_DIR / "sentences.csv"
TOKENS_OUT = RESULTS_DIR / "tokens.csv"


def ensure_results_dir() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(
            f"Corpus file not found at {path}. Expected at: data/grimms.txt"
        )
    # utf-8-sig tolerates BOM; errors='replace' prevents crashes on weird chars
    return path.read_text(encoding="utf-8-sig", errors="replace")


def load_spacy_model() -> spacy.language.Language:
    """
    Loads an English spaCy model. If missing, prints install instructions.
    """
    model_name = "en_core_web_sm"
    try:
        return spacy.load(model_name)
    except OSError as e:
        msg = (
            f"spaCy model '{model_name}' is not installed.\n\n"
            "Install it with:\n"
            "  python -m spacy download en_core_web_sm\n\n"
            "Then re-run:\n"
            "  python code/01_preprocess.py\n"
        )
        raise RuntimeError(msg) from e


def write_sentences(doc: spacy.tokens.Doc) -> list[tuple[int, str]]:
    """
    Returns a list of (sentence_id, sentence_text) and writes to CSV.
    """
    sentences: list[tuple[int, str]] = []
    with SENTENCES_OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sentence_id", "sentence_text"])
        for i, sent in enumerate(doc.sents):
            text = sent.text.strip()
            if not text:
                continue
            sentences.append((i, text))
            writer.writerow([i, text])
    return sentences


def write_tokens(doc: spacy.tokens.Doc) -> None:
    """
    Writes one row per token with linguistic annotations to CSV.
    """
    with TOKENS_OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "sentence_id",
                "token_i",
                "token",
                "lemma",
                "pos",
                "tag",
                "dep",
                "head",
                "is_alpha",
                "is_stop",
            ]
        )

        for sent_id, sent in enumerate(doc.sents):
            for token_i, tok in enumerate(sent):
                writer.writerow(
                    [
                        sent_id,
                        token_i,
                        tok.text,
                        tok.lemma_,
                        tok.pos_,
                        tok.tag_,
                        tok.dep_,
                        tok.head.text,
                        int(tok.is_alpha),
                        int(tok.is_stop),
                    ]
                )


def sanity_checks(doc: spacy.tokens.Doc) -> None:
    """
    Print a few lemma sanity checks so you can confirm the pipeline is working.
    """
    targets = {"took", "ate", "fell", "threw", "killed", "drowned", "burnt", "burned"}
    hits = []
    for tok in doc:
        if tok.text.lower() in targets and tok.pos_ == "VERB":
            hits.append((tok.text, tok.lemma_, tok.pos_))
            if len(hits) >= 15:
                break

    print("\nSanity check: sample verb surface forms → lemmas")
    if not hits:
        print("  (No target verb forms found in the corpus sample.)")
    else:
        for text, lemma, pos in hits:
            print(f"  {text:>10} → {lemma:<10} ({pos})")


def main() -> int:
    ensure_results_dir()
    text = load_text(DATA_PATH)

    nlp = load_spacy_model()

    # Slight speed/memory help: we only need these components
    # (keep parser because we want sentence boundaries + dependencies)
    # If your text is huge, we could use nlp.pipe; Grimm is small enough.
    doc = nlp(text)

    # Write outputs
    _ = write_sentences(doc)
    write_tokens(doc)

    print(f"\nWrote: {SENTENCES_OUT}")
    print(f"Wrote: {TOKENS_OUT}")
    sanity_checks(doc)
    print("\nDone.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        raise
