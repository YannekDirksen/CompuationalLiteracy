#!/usr/bin/env python3
"""
02_detect_lexicon_hits.py

Loads:
- results/tokens.csv
- results/sentences.csv
- lexicons/transgression.json
- lexicons/punishment.json
(optional, if present)
- lexicons/reward.json

Creates:
- results/sentence_hits.csv   (one row per sentence with hit counts + lists)
- results/token_hits.csv      (token-level table filtered to lexicon matches)

Notes:
- Matches lemma by POS category:
    VERB -> verbs
    NOUN/PROPN -> nouns
    ADJ -> adjectives
    ADV -> adverbs
- If a lemma matches multiple lexicons, it is marked as "both" (or "triple" if reward is used).
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Set, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOKENS_IN = PROJECT_ROOT / "results" / "tokens.csv"
SENTENCES_IN = PROJECT_ROOT / "results" / "sentences.csv"

TRANS_LEX = PROJECT_ROOT / "lexicons" / "transgression.json"
PUN_LEX = PROJECT_ROOT / "lexicons" / "punishment.json"
REWARD_LEX = PROJECT_ROOT / "lexicons" / "reward.json"  # optional

SENT_HITS_OUT = PROJECT_ROOT / "results" / "sentence_hits.csv"
TOKEN_HITS_OUT = PROJECT_ROOT / "results" / "token_hits.csv"


POS_TO_LEXCAT = {
    "VERB": "verbs",
    "NOUN": "nouns",
    "PROPN": "nouns",
    "ADJ": "adjectives",
    "ADV": "adverbs",
}


def load_lexicon(path: Path) -> Dict[str, Set[str]]:
    """
    Expects JSON like:
    {
      "verbs": [...],
      "nouns": [...],
      "adjectives": [...],
      "adverbs": [...]
    }
    Any missing category is treated as empty.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Lexicon file {path} must contain a JSON object.")

    out: Dict[str, Set[str]] = {}
    for cat in ("verbs", "nouns", "adjectives", "adverbs"):
        vals = data.get(cat, [])
        if vals is None:
            vals = []
        if not isinstance(vals, list) or not all(isinstance(v, str) for v in vals):
            raise ValueError(f"Lexicon file {path} key '{cat}' must be a list of strings.")
        out[cat] = {v.strip().lower() for v in vals if v and v.strip()}

    return out


def load_sentences(path: Path) -> dict[int, str]:
    sentences: dict[int, str] = {}
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = int(row["sentence_id"])
            sentences[sid] = row["sentence_text"]
    return sentences


def lexicon_has(lex: Dict[str, Set[str]], lex_cat: str, lemma: str) -> bool:
    return lemma in lex.get(lex_cat, set())


def main() -> None:
    if not TOKENS_IN.exists():
        raise FileNotFoundError(f"Missing {TOKENS_IN}. Run code/01_preprocess.py first.")
    if not SENTENCES_IN.exists():
        raise FileNotFoundError(f"Missing {SENTENCES_IN}. Run code/01_preprocess.py first.")
    if not TRANS_LEX.exists() or not PUN_LEX.exists():
        raise FileNotFoundError("Missing lexicon JSON files in lexicons/. Create transgression.json and punishment.json first.")

    trans = load_lexicon(TRANS_LEX)
    pun = load_lexicon(PUN_LEX)

    reward: Optional[Dict[str, Set[str]]] = None
    use_reward = REWARD_LEX.exists()
    if use_reward:
        reward = load_lexicon(REWARD_LEX)

    sentences = load_sentences(SENTENCES_IN)

    # Accumulators per sentence (store lemmas as lists for readability)
    trans_hits = defaultdict(list)   # sid -> list[str]
    pun_hits = defaultdict(list)     # sid -> list[str]
    reward_hits = defaultdict(list)  # sid -> list[str] (optional)

    token_hits_rows = []

    with TOKENS_IN.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = int(row["sentence_id"])
            token = row["token"]
            lemma = (row["lemma"] or "").lower().strip()
            pos = (row["pos"] or "").strip()

            if not lemma:
                continue

            lex_cat = POS_TO_LEXCAT.get(pos)
            if not lex_cat:
                continue  # ignore other POS (DET, ADP, PRON, etc.)

            in_trans = lexicon_has(trans, lex_cat, lemma)
            in_pun = lexicon_has(pun, lex_cat, lemma)
            in_reward = False
            if use_reward and reward is not None:
                in_reward = lexicon_has(reward, lex_cat, lemma)

            if not (in_trans or in_pun or in_reward):
                continue

            # sentence accumulators
            if in_trans:
                trans_hits[sid].append(lemma)
            if in_pun:
                pun_hits[sid].append(lemma)
            if in_reward:
                reward_hits[sid].append(lemma)

            # hit_type label
            hit_labels = []
            if in_trans:
                hit_labels.append("transgression")
            if in_pun:
                hit_labels.append("punishment")
            if in_reward:
                hit_labels.append("reward")

            if len(hit_labels) == 1:
                hit_type = hit_labels[0]
            elif len(hit_labels) == 2:
                hit_type = "both"
            else:
                hit_type = "triple"

            token_hits_rows.append(
                {
                    "sentence_id": sid,
                    "token": token,
                    "lemma": lemma,
                    "pos": pos,
                    "lex_cat": lex_cat,
                    "hit_type": hit_type,
                    "hit_labels": "|".join(hit_labels),
                }
            )

    # Write token-level hits
    with TOKEN_HITS_OUT.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["sentence_id", "token", "lemma", "pos", "lex_cat", "hit_type", "hit_labels"]
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
        ]

        if use_reward:
            fieldnames.append("reward_hit_count")

        fieldnames += [
            "transgression_lemmas",
            "punishment_lemmas",
        ]

        if use_reward:
            fieldnames.append("reward_lemmas")

        fieldnames += [
            "any_hit",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for sid in sorted(sentences.keys()):
            t = trans_hits.get(sid, [])
            p = pun_hits.get(sid, [])
            r = reward_hits.get(sid, []) if use_reward else []

            row_out = {
                "sentence_id": sid,
                "sentence_text": sentences[sid],
                "transgression_hit_count": len(t),
                "punishment_hit_count": len(p),
                "transgression_lemmas": " ".join(t),
                "punishment_lemmas": " ".join(p),
                "any_hit": int(bool(t) or bool(p) or (bool(r) if use_reward else False)),
            }

            if use_reward:
                row_out["reward_hit_count"] = len(r)
                row_out["reward_lemmas"] = " ".join(r)

            writer.writerow(row_out)

    print(f"Wrote: {TOKEN_HITS_OUT}")
    print(f"Wrote: {SENT_HITS_OUT}")

    # quick summary
    total_sents = len(sentences)
    hit_sents = sum(
        1
        for sid in sentences
        if trans_hits.get(sid) or pun_hits.get(sid) or (reward_hits.get(sid) if use_reward else False)
    )
    print(f"Sentences total: {total_sents}")
    print(f"Sentences with any hit: {hit_sents} ({hit_sents/total_sents:.1%})")
    if use_reward:
        rew_sents = sum(1 for sid in sentences if reward_hits.get(sid))
        print(f"Sentences with reward hit: {rew_sents} ({rew_sents/total_sents:.1%})")


if __name__ == "__main__":
    main()
