#!/usr/bin/env python3
"""
00_lexicon_frequencies.py

Counts how often lemmas from the lexicons occur in the corpus.

Lexicons:
- transgression_events.json (verbs)
- punishment_events.json (verbs)
- moral_framing.json (mixed POS)

Input:
- results/tokens.csv

Output:
- printed frequency tables
"""

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "results" / "tokens.csv"

TRANS = ROOT / "lexicons" / "transgression.json"
PUN = ROOT / "lexicons" / "punishment.json"
FRAME = ROOT / "lexicons" / "moral_framing.json"


def load_lexicon(path, key):
    data = json.loads(path.read_text(encoding="utf-8"))
    return set(data[key])


def main():
    if not TOKENS.exists():
        raise FileNotFoundError("Missing results/tokens.csv")

    trans_verbs = load_lexicon(TRANS, "verbs")
    pun_verbs = load_lexicon(PUN, "verbs")
    framing_cues = load_lexicon(FRAME, "cues")

    trans_counts = Counter()
    pun_counts = Counter()
    framing_counts = Counter()

    with TOKENS.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            lemma = (row["lemma"] or "").lower()
            pos = row["pos"]

            if not lemma:
                continue

            # transgression & punishment = verbs only
            if pos == "VERB":
                if lemma in trans_verbs:
                    trans_counts[lemma] += 1
                if lemma in pun_verbs:
                    pun_counts[lemma] += 1

            # moral framing = any POS
            if lemma in framing_cues:
                framing_counts[lemma] += 1

    print("\n=== Transgression verbs ===")
    for lemma, count in trans_counts.most_common():
        print(f"{lemma:>12}: {count}")

    print("\n=== Punishment verbs ===")
    for lemma, count in pun_counts.most_common():
        print(f"{lemma:>12}: {count}")

    print("\n=== Moral framing cues (all POS) ===")
    for lemma, count in framing_counts.most_common():
        print(f"{lemma:>12}: {count}")


if __name__ == "__main__":
    main()
