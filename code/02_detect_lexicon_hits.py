#!/usr/bin/env python3
"""
02_detect_lexicon_hits.py

Loads:
- results/tokens.csv
- lexicons/transgression.json
- lexicons/punishment.json

Creates:
- results/sentence_hits.csv   (one row per sentence with hit counts + lists)
- results/token_hits.csv      (token-level table filtered to lexicon matches)
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOKENS_IN = PROJECT_ROOT / "results" / "tokens.csv"
SENTENCES_IN = PROJECT_ROOT / "results" / "sentences.csv"

TRANS_LEX = PROJECT_ROOT / "lexicons" / "transgression.json"
PUN_LEX = PROJECT_ROOT / "lexicons" / "punishment.json"

SENT_HITS_OUT = PROJECT_ROOT / "results" / "sentence_hits.csv"
TOKEN_HITS_OUT = PROJECT_ROOT / "results" / "token_hits.csv"


def load_lexicon(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    verbs = data.get("verbs", [])
    if not isinstance(verbs, list) or not all(isinstance(v, str) for v in verbs):
        raise ValueError(f"Lexicon file {path} must contain a JSON object with a 'verbs' list of strings.")
    return {v.strip().lower() for v in verbs if v.strip()}


def load_sentences(path: Path) -> dict[int, str]:
    sentences: dict[int, str] = {}
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = int(row["sentence_id"])
            sentences[sid] = row["sentence_text"]
    return sentences


def main() -> None:
    if not TOKENS_IN.exists():
        raise FileNotFoundError(f"Missing {TOKENS_IN}. Run code/01_preprocess.py first.")
    if not SENTENCES_IN.exists():
        raise FileNotFoundError(f"Missing {SENTENCES_IN}. Run code/01_preprocess.py first.")
    if not TRANS_LEX.exists() or not PUN_LEX.exists():
        raise FileNotFoundError("Missing lexicon JSON files in lexicons/. Create transgression.json and punishment.json first.")

    trans = load_lexicon(TRANS_LEX)
    pun = load_lexicon(PUN_LEX)
    sentences = load_sentences(SENTENCES_IN)

    # Accumulators per sentence
    trans_hits = defaultdict(list)  # sid -> list of lemmas
    pun_hits = defaultdict(list)    # sid -> list of lemmas

    token_hits_rows = []

    with TOKENS_IN.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = int(row["sentence_id"])
            token = row["token"]
            lemma = row["lemma"].lower()
            pos = row["pos"]

            # Only consider verbs (keeps noise down)
            if pos != "VERB":
                continue

            hit_type = None
            if lemma in trans:
                trans_hits[sid].append(lemma)
                hit_type = "transgression"
            if lemma in pun:
                pun_hits[sid].append(lemma)
                # If it was already transgression too, mark as both
                hit_type = "both" if hit_type else "punishment"

            if hit_type:
                token_hits_rows.append(
                    {
                        "sentence_id": sid,
                        "token": token,
                        "lemma": lemma,
                        "hit_type": hit_type,
                    }
                )

    # Write token-level hits
    with TOKEN_HITS_OUT.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["sentence_id", "token", "lemma", "hit_type"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(token_hits_rows)

    # Write sentence-level table
    with SENT_HITS_OUT.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "sentence_id",
            "sentence_text",
            "transgression_hit_count",
            "punishment_hit_count",
            "transgression_lemmas",
            "punishment_lemmas",
            "any_hit",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # iterate over all sentences so you can compute rates properly
        for sid in sorted(sentences.keys()):
            t = trans_hits.get(sid, [])
            p = pun_hits.get(sid, [])
            writer.writerow(
                {
                    "sentence_id": sid,
                    "sentence_text": sentences[sid],
                    "transgression_hit_count": len(t),
                    "punishment_hit_count": len(p),
                    "transgression_lemmas": " ".join(t),
                    "punishment_lemmas": " ".join(p),
                    "any_hit": int(bool(t) or bool(p)),
                }
            )

    print(f"Wrote: {TOKEN_HITS_OUT}")
    print(f"Wrote: {SENT_HITS_OUT}")

    # quick summary
    total_sents = len(sentences)
    hit_sents = sum(1 for sid in sentences if trans_hits.get(sid) or pun_hits.get(sid))
    print(f"Sentences total: {total_sents}")
    print(f"Sentences with any hit: {hit_sents} ({hit_sents/total_sents:.1%})")


if __name__ == "__main__":
    main()
