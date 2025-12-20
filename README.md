# Morality, Transgression, and Punishment in Grimm’s Fairy Tales

This project studies how **morality is expressed in Grimm’s fairy tales** using simple computational methods.

The focus is on three moral categories:
- **Transgression** (doing something wrong)
- **Punishment** (negative consequences)
- **Reward** (positive outcomes or restoration)

The project uses a lexicon-based pipeline to analyse how often these categories appear in the texts and how they are distributed across sentences.

---

## Research question

**How are transgression, punishment, and reward expressed in the language of Grimm’s fairy tales, and how are they distributed across the narratives?**

This is a humanities research question. Computational methods are used as tools to support analysis, not to replace interpretation.

---

## Data

- The dataset consists of English translations of Grimm’s fairy tales.
- The basic unit of analysis is the **sentence**.
- The corpus is included in the repository so that the analysis can be reproduced.

---
## Methodological approach
To analyse morality in the Grimm corpus, I use a theory-guided lexicon-based approach. 
Based on Roberts’ analysis of fairy tales as narratives that enforce social norms by rewarding good behaviour and punishing wrongdoing, I distinguish three semantic categories: transgression, punishment, and reward. 
These categories reflect the moral logic of fairy tales, in which norm violations lead to negative consequences and moral order is eventually restored.

Each category is represented by a curated lexicon consisting of verbs, nouns, adjectives, and adverbs that are associated with norm violation, punishment, or positive moral outcomes. 
The lexicons are not intended to represent meaning exhaustively. Instead, they are used as heuristic indicators of moral functions in the text.

Interpretation is based on the distribution and co-occurrence of lexicon items in the corpus, rather than on individual words in isolation. 
In particular, attention is paid to how transgression and punishment markers appear in relation to each other across sentences.

This approach follows earlier corpus-based studies of violence in Grimm’s fairy tales, which operationalise abstract semantic concepts through lexical frequency and contextual analysis rather than simple word counts. 
Accordingly, the results are interpreted as narrative patterns, not as direct semantic classifications of individual sentences.
---
## Pipeline description

The project follows a complete pipeline from raw text to analytical results.

### 01_preprocess.py
- Reads the raw text files
- Splits texts into sentences
- Tokenises the text
- Applies lemmatisation and part-of-speech tagging using spaCy
- Outputs:
  - `results/sentences.csv`
  - `results/tokens.csv`

### 02_detect_lexicon_hits.py
- Loads lexicons for:
  - transgression
  - punishment
  - reward
- Matches token lemmas to lexicons based on part of speech
- Allows overlap between categories (for example, *kill* can be both transgression and punishment)
- Outputs:
  - `results/sentence_hits.csv`
  - `results/token_hits.csv`

### 03_analysis.py
- Aggregates sentence-level and token-level results
- Computes descriptive statistics
- Produces plots
- Outputs:
  - `results/analysis_summary.txt`
  - figures in `results/figures/`

### 04_show_sentences_by_lemma.py
- Helper script for qualitative inspection
- Displays example sentences containing a chosen lemma
- Used to check false positives and improve lexicons

---

## Lexicons

Lexicons are stored in the `lexicons/` folder as JSON files:
- `transgression.json`
- `punishment.json`
- `reward.json`

Each lexicon is divided by part of speech:
- verbs
- nouns
- adjectives
- adverbs

The lexicons were created and **refined iteratively**.  
Words that produced many false positives (for example *take*, *fall*, *fire*) were removed after manual inspection of example sentences.

The lexicons are **heuristic tools**, not complete representations of moral meaning.

---

## Results (short summary)

Main observations:
- Transgression and punishment appear at similar rates at the sentence level.
- Reward appears less often than transgression or punishment.
- Most sentences contain at most one moral category.
- Moral processes usually unfold across multiple sentences, not within a single sentence.

This suggests that morality in fairy tales is **narrative and sequential**, not sentence-based.

---

## Evaluation and Reliability

To assess the reliability of the lexicon-based classification, a small manual
precision evaluation was conducted. Sentence-level outputs are known to be
particularly sensitive to overgeneration in narrative texts, making explicit
evaluation necessary.

### Sampling procedure

Fifty sentences labeled as **transgression** and fifty sentences labeled as
**punishment** were randomly sampled from `results/sentence_hits.csv` using the
helper script `code/04_show_sentences_by_category.py`. The sentences were
inspected in their narrative context.

Each sentence was manually classified into one of three categories:

- **Relevant**: clearly expresses a moral transgression or punishment
- **Ambiguous**: potentially expresses a transgression or punishment, but
  requires broader narrative context or interpretation
- **Not relevant**: contains no moral transgression or punishment despite a
  lexicon match

This three-way distinction reflects the interpretive nature of moral meaning in
folklore narratives.

### Precision results

| Category      | Relevant | Ambiguous | Not relevant | Strict precision | Lenient precision |
|--------------|----------|-----------|--------------|------------------|-------------------|
| Transgression | 24       | 5         | 21           | 48%              | 58%               |
| Punishment    | 10       | 6         | 34           | 20%              | 32%               |

Strict precision counts only **Relevant** cases as correct, while lenient
precision additionally includes **Ambiguous** cases.

### Interpretation

The evaluation reveals a clear asymmetry between transgression and punishment.
Transgressive acts in Grimm’s Fairy Tales are more frequently encoded through
explicit actions such as theft, deception, or violence, leading to moderate
sentence-level precision.

Punishment, by contrast, is often expressed indirectly through grief, illness,
shame, exile, or karmic and supernatural consequences. These forms of punishment
are frequently distributed across multiple sentences or implied by narrative
outcome rather than marked by explicit punitive verbs. As a result, sentence-level
detection of punishment exhibits lower precision.

Many false positives arise from high-frequency or semantically light lexical
items (e.g. *eat*, *lie*, *die*), illustrating a key limitation of lexicon-based
approaches. The results therefore suggest that moral meaning in Grimm’s Fairy
Tales is primarily established at the discourse level rather than at the level
of individual sentences.

Overall, the lexicon-based pipeline should be understood as a method for
identifying candidate passages for further qualitative analysis rather than as
a definitive classifier of moral events.

---

## Limitations and potential bias

This project has several limitations:
- Lexicon-based methods cannot detect implicit or indirect morality.
- Polysemous words can still cause noise.
- Sentence-level analysis may miss long-range narrative structure.
- Errors in POS tagging or lemmatisation affect later steps.
- English translations may differ from the original German texts.

These limitations are acknowledged and discussed in the analysis.

---

## Reproducibility

To run the full pipeline:

```bash
python code/01_preprocess.py
python code/02_detect_lexicon_hits.py
python code/03_analysis.py
