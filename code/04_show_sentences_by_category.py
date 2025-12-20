#!/usr/bin/env python3
"""
04_show_sentences_by_category.py

Print random sentence examples from sentence_hits.csv by category.

Categories:
- transgression
- punishment
- both
- none
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SENT_HITS = ROOT / "results" / "sentence_hits.csv"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python 04_show_sentences_by_category.py <category> [n]")
        return 2

    category = sys.argv[1].lower()
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    if not SENT_HITS.exists():
        raise FileNotFoundError("results/sentence_hits.csv not found. Run 02_detect_lexicon_hits.py first.")

    rows = []
    with SENT_HITS.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["transgression_hit_count"] = int(r["transgression_hit_count"])
            r["punishment_hit_count"] = int(r["punishment_hit_count"])
            rows.append(r)

    if category == "transgression":
        subset = [r for r in rows if r["transgression_hit_count"] > 0 and r["punishment_hit_count"] == 0]
    elif category == "punishment":
        subset = [r for r in rows if r["punishment_hit_count"] > 0 and r["transgression_hit_count"] == 0]
    elif category == "both":
        subset = [r for r in rows if r["punishment_hit_count"] > 0 and r["transgression_hit_count"] > 0]
    elif category == "none":
        subset = [r for r in rows if r["punishment_hit_count"] == 0 and r["transgression_hit_count"] == 0]
    else:
        print("Category must be: transgression | punishment | both | none")
        return 2

    random.shuffle(subset)
    sample = subset[: min(n, len(subset))]

    print(f"\nCategory '{category}' — showing {len(sample)} of {len(subset)} sentences:\n")
    for r in sample:
        print(f"[{r['sentence_id']}]")
        print(r["sentence_text"])
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
