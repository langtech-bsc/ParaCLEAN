# Translation Data Processing Pipeline

## Overview

This project provides a modular pipeline for preparing parallel corpora for machine translation research.\
It standardises preprocessing across datasets, making it easier to train and evaluate translation models on consistent, high-quality data.

The pipeline is:

- **Modular** – enable or disable steps as needed.
- **Configurable** – control all behaviour via a YAML config file.
- **Reproducible** – consistent outputs for large-scale experiments.
- **Scalable** – runs on laptops or HPC clusters with optional parallelisation.

---

## Features

- **Input handling**: Read corpora in plain text (`.txt`) or tab-separated (`.tsv`) formats.
- **Embeddings**: Compute multilingual sentence embeddings (e.g. LaBSE, SONAR).
- **Language ID**: Detect and filter sentences by language.
- **Filtering**: Filter by embedding scores, sentence ratios, and language probability.
- **Deduplication**: Remove duplicate sentence pairs and fuzzy matches across corpora.
- **Bifixer**: Apply any of bifixer's functionality. Default is to ignore deduplication and segmentation.
- **Normalisation**: Standardise punctuation, spacing, and casing.

---

## Prerequisites

- Python ≥3.8
- Sufficient disk space (embeddings can be large).
- (Optional) HPC cluster or multi-core machine for parallel processing.

---

## Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/langtech-bsc/ParaCLEAN
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

## Configuration

The pipeline is configured via a YAML file. Example config files are provided for both single and multi file inputs. Below is a single file example:

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
model_path: null   # optional, if you want to point to a local model path

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

# Input corpus (single)
input: ["data-storage/Europarl.es-de.es", "data-storage/Europarl.es-de.de"]
format: "plain_text"  # or "tsv"
```
## Pipeline Steps
**input** Preprocesses and normalises the raw input format.

**embeddings** Computes sentence embeddings for later filtering.

**langid** Runs language identification to remove sentences in the wrong language.

**filter** Applies heuristics and thresholds (e.g. length ratios, embedding similarity, language ID confidence).

**dedup** Removes duplicate or near-duplicate sentence pairs.

**bifixer** Integrates bifixer functionality. Default: no deduplication/segmentation. Requires an existing installation of bifixer

**normalise** Applies lightweight normalisation to punctuation, casing, etc.

## Outputs

Each step writes intermediate files under the desginated output directory.

## Notes & Caveats

SONAR embeddings: inputs longer than 514 tokens are truncated.

Disk space: embeddings can be large; ensure sufficient space.

Extensibility: filtering and normalisation rules can be customised by editing the corresponding modules in steps/ or adding language-specific rules in `normalisation`

## Development

To add a new processing step:

1. Create a module in steps/.
2. Define a function with a consistent interface.
3. Register it in pipeline.py.

## License


## Citation

```bibtex
@software{translation_pipeline,
  author = {Your Name},
  title = {Translation Data Processing Pipeline},
  year = {2025},
  url = {https://github.com/<your-repo>}
}
```
