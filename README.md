# ParaCLEAN

Parallel Corpus LanguagE Alignment and Normalisation

# Cleaning pipeline for parallel sentence datasets

This pipeline has been developed in order to provide a tool for the analysis and subsequent filtering of parallel datasets used for training and fine-tuning of MT-engines.

The pipeline works in two steps:

- **Step 1: Scoring**
  
  Sentences are scored with LaBSE (<https://github.com/bojone/labse>) for alignment and with the python library for language detection lingua.py (<https://github.com/pemistahl/lingua-py>) for language probability.

- **Step 2: Filtering**
  
  Sentences are filtered basing on
  - a threshold for alignment: 0.75 LaBSE
  - a threshold for language probability: 0.50 lingua.py

  These thresholds can be adjusted depending on the specific needs/project.

  Sentences are filtered with Bifixer https://github.com/bitextor/bifixer
  Bifixer parameters are all the default ones, but --aggressive_dedup.

**How to use the pipeline:**

- Activate the virtual environment: source use_venv_pipeline.sh

- **Step 1:**
  
  python scoring/labse_score_store.py --metadata /gpfs/projects/bsc88/data/02-metadata/pangeanic-clean_ca-en_20230830.json

- **Step 2:**
  
  python sampling/sampler.py /gpfs/projects/bsc88/data/03-mt-repository/pangeanic-clean_ca-en_20230830/pangeanic-clean_ca-en_20230830.scored --l1 ca --l2 en --sample_output_path /gpfs/projects/bsc88/data/04-mt-samplings/mt-aina-pangeanic-clean_ca-en_1.0

