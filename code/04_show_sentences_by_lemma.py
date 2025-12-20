#!/usr/bin/env python3
"""
04_show_sentences_by_lemma.py

Prints random sentences that contain a given VERB lemma (e.g., 'take').
Uses:
- results/tokens.csv (to find lemma occurrences)
- results/sentences.csv (to print the full sentence)

Usage examples:
  python code/04_show_sentences_by_lemma.py take 25
  python code/04_show_sentences_by_lemma.py die 20
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "results" / "tokens.csv"
SENTS = ROOT / "results" / "sentences.csv"


def load_sentences() -> dict[int, str]:
    out = {}
    with SENTS.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[int(r["sentence_id"])] = r["sentence_text"]
    return out


def collect_sentence_ids_for_lemma(target_lemma: str) -> set[int]:
    sids = set()
    with TOKENS.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["pos"] != "VERB":
                continue
            if (r["lemma"] or "").lower() == target_lemma:
                sids.add(int(r["sentence_id"]))
    return sids


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python code/04_show_sentences_by_lemma.py <lemma> [n]", file=sys.stderr)
        return 2

    lemma = sys.argv[1].lower().strip()
    n = int(sys.argv[2]) if len(sys.argv) >= 3 else 20

    if not TOKENS.exists() or not SENTS.exists():
        raise FileNotFoundError("Missing results/tokens.csv or results/sentences.csv. Run 01_preprocess.py first.")

    sentences = load_sentences()
    sids = sorted(collect_sentence_ids_for_lemma(lemma))

    if not sids:
        print(f"No sentences found containing VERB lemma: {lemma}")
        return 0

    random.shuffle(sids)
    sample = sids[: min(n, len(sids))]

    print(f"\nFound {len(sids)} sentences containing VERB lemma '{lemma}'. Showing {len(sample)} random examples:\n")
    for sid in sample:
        print(f"[{sid}] {sentences.get(sid, '').strip()}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
