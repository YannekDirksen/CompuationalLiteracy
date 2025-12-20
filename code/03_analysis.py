#!/usr/bin/env python3
"""
03_analysis.py

Analysis + plots for Grimm morality/punishment/reward lexicon pipeline.

Inputs:
- results/sentence_hits.csv
- results/token_hits.csv

Outputs:
- results/analysis_summary.txt
- results/figures/*.png

Notes:
- Uses matplotlib (no seaborn).
- Keeps plots simple and interpretable.
- Automatically adapts if reward columns are present.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SENT_HITS = PROJECT_ROOT / "results" / "sentence_hits.csv"
TOKEN_HITS = PROJECT_ROOT / "results" / "token_hits.csv"

RESULTS_DIR = PROJECT_ROOT / "results"
FIG_DIR = RESULTS_DIR / "figures"
SUMMARY_OUT = RESULTS_DIR / "analysis_summary.txt"


def ensure_dirs() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)


def load_sentence_hits(path: Path) -> tuple[list[dict], bool]:
    """
    Returns (rows, has_reward_columns).
    """
    rows = []
    has_reward = False

    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        has_reward = "reward_hit_count" in fieldnames

        for r in reader:
            r["sentence_id"] = int(r["sentence_id"])
            r["transgression_hit_count"] = int(r["transgression_hit_count"])
            r["punishment_hit_count"] = int(r["punishment_hit_count"])
            if has_reward:
                r["reward_hit_count"] = int(r.get("reward_hit_count", 0))
            r["any_hit"] = int(r["any_hit"])
            rows.append(r)

    return rows, has_reward


def load_token_hits(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            r["sentence_id"] = int(r["sentence_id"])
            r["lemma"] = (r.get("lemma") or "").lower().strip()
            r["hit_type"] = (r.get("hit_type") or "").lower().strip()
            # hit_labels is optional, but nice if present
            r["hit_labels"] = (r.get("hit_labels") or "").lower().strip()
            rows.append(r)
    return rows


def top_n(counter: Counter, n: int = 15) -> list[tuple[str, int]]:
    return counter.most_common(n)


def write_summary(text: str) -> None:
    SUMMARY_OUT.write_text(text, encoding="utf-8")


def bar_plot(items: list[tuple[str, int]], title: str, outpath: Path) -> None:
    if not items:
        return
    labels = [k for k, _ in items]
    values = [v for _, v in items]

    plt.figure()
    plt.bar(labels, values)
    plt.title(title)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()


def main() -> None:
    ensure_dirs()

    if not SENT_HITS.exists():
        raise FileNotFoundError(f"Missing {SENT_HITS}. Run code/02_detect_lexicon_hits.py first.")
    if not TOKEN_HITS.exists():
        raise FileNotFoundError(f"Missing {TOKEN_HITS}. Run code/02_detect_lexicon_hits.py first.")

    sent_rows, has_reward = load_sentence_hits(SENT_HITS)
    token_rows = load_token_hits(TOKEN_HITS)

    total_sents = len(sent_rows)
    any_hit = sum(r["any_hit"] for r in sent_rows)
    trans_sents = sum(1 for r in sent_rows if r["transgression_hit_count"] > 0)
    pun_sents = sum(1 for r in sent_rows if r["punishment_hit_count"] > 0)
    both_sents = sum(
        1 for r in sent_rows
        if r["transgression_hit_count"] > 0 and r["punishment_hit_count"] > 0
    )

    reward_sents = 0
    if has_reward:
        reward_sents = sum(1 for r in sent_rows if r["reward_hit_count"] > 0)
        triple_sents = sum(
            1 for r in sent_rows
            if r["transgression_hit_count"] > 0 and r["punishment_hit_count"] > 0 and r["reward_hit_count"] > 0
        )
    else:
        triple_sents = 0

    # Token-level frequency counts
    trans_token_lemmas = Counter()
    pun_token_lemmas = Counter()
    reward_token_lemmas = Counter()
    both_token_lemmas = Counter()      # for hit_type == "both"
    triple_token_lemmas = Counter()    # for hit_type == "triple" (if present)

    for r in token_rows:
        lemma = r["lemma"]
        hit_type = r["hit_type"]
        if not lemma:
            continue

        if hit_type == "transgression":
            trans_token_lemmas[lemma] += 1
        elif hit_type == "punishment":
            pun_token_lemmas[lemma] += 1
        elif hit_type == "reward":
            reward_token_lemmas[lemma] += 1
        elif hit_type == "both":
            both_token_lemmas[lemma] += 1
        elif hit_type == "triple":
            triple_token_lemmas[lemma] += 1

    # Sentence-level distribution of counts
    trans_count_dist = Counter(r["transgression_hit_count"] for r in sent_rows)
    pun_count_dist = Counter(r["punishment_hit_count"] for r in sent_rows)
    reward_count_dist = Counter(r["reward_hit_count"] for r in sent_rows) if has_reward else Counter()

    # Summary text
    lines = []
    lines.append("Grimm lexicon pipeline — analysis summary\n")
    lines.append(f"Total sentences: {total_sents}")
    lines.append(f"Sentences with ANY lexicon hit: {any_hit} ({any_hit/total_sents:.1%})")
    lines.append(f"Sentences with TRANSGRESSION hit: {trans_sents} ({trans_sents/total_sents:.1%})")
    lines.append(f"Sentences with PUNISHMENT hit: {pun_sents} ({pun_sents/total_sents:.1%})")
    lines.append(f"Sentences with BOTH transgression & punishment hits: {both_sents} ({both_sents/total_sents:.1%})")

    if has_reward:
        lines.append(f"Sentences with REWARD hit: {reward_sents} ({reward_sents/total_sents:.1%})")
        lines.append(f"Sentences with TRIPLE (transgression+punishment+reward): {triple_sents} ({triple_sents/total_sents:.1%})")

    lines.append("")

    lines.append("Top transgression lemmas (token-level):")
    for lemma, c in top_n(trans_token_lemmas, 15):
        lines.append(f"  {lemma:<12} {c}")
    lines.append("")

    lines.append("Top punishment lemmas (token-level):")
    for lemma, c in top_n(pun_token_lemmas, 15):
        lines.append(f"  {lemma:<12} {c}")
    lines.append("")

    if has_reward:
        lines.append("Top reward lemmas (token-level):")
        for lemma, c in top_n(reward_token_lemmas, 15):
            lines.append(f"  {lemma:<12} {c}")
        lines.append("")

    if both_token_lemmas:
        lines.append("Overlapping lemmas marked as BOTH (token-level):")
        for lemma, c in top_n(both_token_lemmas, 15):
            lines.append(f"  {lemma:<12} {c}")
        lines.append("")

    if triple_token_lemmas:
        lines.append("Overlapping lemmas marked as TRIPLE (token-level):")
        for lemma, c in top_n(triple_token_lemmas, 15):
            lines.append(f"  {lemma:<12} {c}")
        lines.append("")

    lines.append("Distribution: transgression_hit_count per sentence (count -> #sentences)")
    for k in sorted(trans_count_dist.keys()):
        lines.append(f"  {k:>2} -> {trans_count_dist[k]}")
    lines.append("")

    lines.append("Distribution: punishment_hit_count per sentence (count -> #sentences)")
    for k in sorted(pun_count_dist.keys()):
        lines.append(f"  {k:>2} -> {pun_count_dist[k]}")
    lines.append("")

    if has_reward:
        lines.append("Distribution: reward_hit_count per sentence (count -> #sentences)")
        for k in sorted(reward_count_dist.keys()):
            lines.append(f"  {k:>2} -> {reward_count_dist[k]}")
        lines.append("")

    summary_text = "\n".join(lines)
    print(summary_text)
    write_summary(summary_text)
    print(f"Wrote: {SUMMARY_OUT}")

    # --- Plots ---
    # 1) Sentence coverage bar chart
    coverage_labels = ["Any hit", "Transgression", "Punishment", "Both"]
    coverage_values = [any_hit, trans_sents, pun_sents, both_sents]

    if has_reward:
        coverage_labels += ["Reward", "Triple"]
        coverage_values += [reward_sents, triple_sents]

    plt.figure()
    plt.bar(coverage_labels, coverage_values)
    plt.title("Sentence coverage: lexicon hits")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "coverage_sentences.png", dpi=200)
    plt.close()

    # 2) Top transgression lemmas
    bar_plot(
        top_n(trans_token_lemmas, 15),
        "Top transgression lemmas (token hits)",
        FIG_DIR / "top_transgression_lemmas.png",
    )

    # 3) Top punishment lemmas
    bar_plot(
        top_n(pun_token_lemmas, 15),
        "Top punishment lemmas (token hits)",
        FIG_DIR / "top_punishment_lemmas.png",
    )

    # 4) Top reward lemmas (if present)
    if has_reward:
        bar_plot(
            top_n(reward_token_lemmas, 15),
            "Top reward lemmas (token hits)",
            FIG_DIR / "top_reward_lemmas.png",
        )

    # 5) BOTH / TRIPLE overlap plots
    if both_token_lemmas:
        bar_plot(
            top_n(both_token_lemmas, 15),
            "Overlapping lemmas (hit_type = BOTH)",
            FIG_DIR / "overlap_both_lemmas.png",
        )

    if triple_token_lemmas:
        bar_plot(
            top_n(triple_token_lemmas, 15),
            "Overlapping lemmas (hit_type = TRIPLE)",
            FIG_DIR / "overlap_triple_lemmas.png",
        )

    # 6) Hit-count distributions
    max_k = 0
    if trans_count_dist:
        max_k = max(max_k, max(trans_count_dist.keys()))
    if pun_count_dist:
        max_k = max(max_k, max(pun_count_dist.keys()))
    if has_reward and reward_count_dist:
        max_k = max(max_k, max(reward_count_dist.keys()))
    max_k = min(max_k, 6)

    # transgression
    trans_x = list(range(0, max_k + 1))
    trans_y = [trans_count_dist.get(k, 0) for k in trans_x]
    plt.figure()
    plt.bar([str(k) for k in trans_x], trans_y)
    plt.title("Transgression hits per sentence (0–6)")
    plt.xlabel("hit count")
    plt.ylabel("# sentences")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "dist_transgression_hits_per_sentence.png", dpi=200)
    plt.close()

    # punishment
    pun_x = list(range(0, max_k + 1))
    pun_y = [pun_count_dist.get(k, 0) for k in pun_x]
    plt.figure()
    plt.bar([str(k) for k in pun_x], pun_y)
    plt.title("Punishment hits per sentence (0–6)")
    plt.xlabel("hit count")
    plt.ylabel("# sentences")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "dist_punishment_hits_per_sentence.png", dpi=200)
    plt.close()

    # reward
    if has_reward:
        rew_x = list(range(0, max_k + 1))
        rew_y = [reward_count_dist.get(k, 0) for k in rew_x]
        plt.figure()
        plt.bar([str(k) for k in rew_x], rew_y)
        plt.title("Reward hits per sentence (0–6)")
        plt.xlabel("hit count")
        plt.ylabel("# sentences")
        plt.tight_layout()
        plt.savefig(FIG_DIR / "dist_reward_hits_per_sentence.png", dpi=200)
        plt.close()

    print(f"Wrote figures to: {FIG_DIR}")


if __name__ == "__main__":
    main()
