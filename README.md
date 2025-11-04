# Translation Data Processing Pipeline

## Overview

This project provides a modular pipeline for preparing parallel sentence-level corpora for machine translation research.\
It standardises preprocessing across datasets, making it easier to train and evaluate translation models on consistent, high-quality data.

The pipeline is:

- **Modular** – enable or disable steps as needed.
- **Configurable** – control all behaviour via a YAML config file.
- **Reproducible** – consistent outputs for large-scale experiments.
- **Scalable** – simple to adapt for parallelisation in an HPC environment.

---

## Features

- **Input handling**: Read corpora in plain text (`.txt`), tab-separated (`.tsv`) or translation memory (`.tmx`) formats.
- **Embeddings**: Compute multilingual sentence embeddings (e.g. LaBSE (default), SONAR (can optionally be added)).
- **Language ID**: Calculate probability that segments are in the desired language (using GlotLID).
- **Filtering**: Filter by user-defined embedding scores and language probability thresholds.
- **Deduplication**: Remove duplicate sentence pairs and fuzzy matches across corpora.
- **Bifixer**: Apply any of Bifixer's functionality. Default is to ignore deduplication and segmentation.
- **Normalisation**: Standardise punctuation, spacing, and casing. Includes easy-to extend language specific normalisation.

---

## Prerequisites

- Python ≥3.8
- Sufficient disk space (embeddings can be large).
- (Optional) HPC cluster or multi-core machine for parallel processing.

---

## Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/paraclean023-coder/ParaCLEAN
cd ParaClean
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```
## Usage
Run the pipeline with a configuration file:

```bash
python pipeline.py --config config_multi.yaml
```
Progress and outputs are logged to the console.
Each step writes intermediate `.tsv` files to the specified output directory.

## Configuration

The pipeline supports both **single-corpus** and **multi-corpus** runs.

- **Single-corpus** runs: one corpus passes sequentially through all selected steps.
- **Multi-corpus** runs: several corpora are processed individually up to the scoring steps, then **merged** for filtering, deduplication, and normalisation.

## Pipeline Steps
**input** Reads and normalises the raw input format.

**embeddings** Computes sentence embeddings for filtering.

**langid** Runs language identification on both sides.

**filter** Applies thresholds for similarity and language probability.

**dedup** Removes exact and near-duplicate sentence pairs.

**bifixer** Runs optional Bifixer cleaning (requires Bifixer installed).

**normalise** Applies final punctuation and spacing normalisation.

### Example: Single-Corpus Run

```yaml
# ===========================
# Pipeline configuration file
# Example: single corpus run
# ===========================

# Output directory (will be created if missing)
output: "data/Europarl"

# Languages
l1: "es"
l2: "de"

# Embedding model (choices: labse, sonar if downloaded)
model: "labse"
model_path: null   # optional, if you want to point to a local model path.

# Filtering thresholds
alignment_score: 0.75
langid_l1_prob: 0.5
langid_l2_prob: 0.5

# Pipeline steps to run (in order)
steps:
  - input
  - embeddings
  - langid
  - filter
  - dedup
  - bifixer
  - normalise

# Optional Bifixer flags. More info can be found at  https://github.com/bitextor/bifixer
bifixer_flags: ["--ignore_segmentation", "--ignore_duplicates"]

# Input corpus (single)
input: ["data-storage/Europarl.es-de.es", "data-storage/Europarl.es-de.de"]
format: "plain_text"  # or "tsv" or "tmx"
```
### Example: Multi-Corpus Run

```yaml
# ===========================
# Pipeline configuration file
# Example: multi-corpus run
# ===========================

output: "testing/multi"

l1: "Catalan"
l2: "cmn_Hani"

model: "labse"
model_path: null

alignment_score: 0.75
langid_l1_prob: 0.5
langid_l2_prob: 0.5

steps:
  - filter
  - dedup
  - bifixer
  - normalise

bifixer_flags: ["--ignore_segmentation", "--ignore_duplicates"]

inputs:
  - name: "TED2020"
    type: "plain_text"
    start_from: "testing/multi/TED2020.embeddings.tsv"
    steps: ["langid"]

  - name: "QED"
    type: "plain_text"
    start_from: "testing/multi/QED.embeddings.tsv"
    steps: ["langid"]
```
Each corpus runs its own per-corpus steps (`input`, `embeddings`, `langid`) before merging.
The merged dataset then passes through `filter`, `dedup`, `bifixer`, and `normalise`.

## Outputs

Each step writes a .tsv file in the specified output directory.
Intermediate files are named after their processing step, e.g.:
```yaml
Europarl.embeddings.tsv
Europarl.langid.tsv
Europarl.filtered.tsv
```

The **final output** (after `normalise`) contains four columns:
1. Source language (original)
2. Target language (original)
3. Source language (normalised)
4. Target language (normalised)

## Language Identifiers

Language codes can be specified flexibly and are resolved internally. 
The following are equivalent for Catalan:
  - Catalan
  - ca
  - ca_Latn
  - cat


## Notes & Caveats

SONAR embeddings: inputs longer than 514 tokens are truncated.

Disk space: embeddings can be large; ensure sufficient space.

Extensibility: filtering and normalisation rules can be customised by editing the corresponding modules in steps/ or adding language-specific rules in `normalisation`

## Development

To add a new processing step:

1. Create a module in steps/ e.g. `steps/my_step.py`).
2. Define a function with a consistent interface (`input_path`, `output_path`, etc.).
3. Register it in `pipeline.py` within the `step_fns` dictionary.

Example:
```python
"my_step": lambda p: my_step.run(current, p + ".my_step.tsv", l1, l2)
```

## License
This project is released under the MIT License
You are free to use, modify, and distribute it with attribution.

## Citation


## Acknowledgements
This project builds upon components and concepts from:

- [Bifixer](https://github.com/bitextor/bifixer)
- [LaBSE](https://huggingface.co/sentence-transformers/LaBSE)
- [SONAR](https://github.com/facebookresearch/SONAR)
- [GlotLID](https://github.com/cisnlp/GlotLID)
