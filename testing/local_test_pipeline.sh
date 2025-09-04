#!/bin/bash

set -e  # exit on any error
umask 007

# ----------------------------
# Set variables and test files
# ----------------------------
l1=ca
l2=ja
data_format=plain_text
split_size=10

formatted="formatted_test.tsv"
scored="scored_test.tsv"

l1_file="/gpfs/projects/bsc88/mt_translation/paraclean/data/raw-corpora/multiccaligned-short_ca-ja_20250904/MultiCCAligned.ca-ja.ca"
l2_file="/gpfs/projects/bsc88/mt_translation/paraclean/data/raw-corpora/multiccaligned-short_ca-ja_20250904/MultiCCAligned.ca-ja.ja"

# filtering thresholds
threshold=0.75
l1_probability=0.5
l2_probability=0.5

# ----------------------------
# Run input_formats.py
# ----------------------------
echo "Running input_formats.py..."
python /gpfs/projects/bsc88/mt_translation/paraclean/input_formats.py \
    --input ${l1_file} ${l2_file} \
    --input_format ${data_format} \
    --l1 ${l1} --l2 ${l2} \
    --format ${formatted} \
    --output scored

# Count number of sentences
size_sentences=$(wc -l < "${formatted}")
echo "Number of sentences: ${size_sentences}"

# ----------------------------
# Split formatted file
# ----------------------------
echo "Splitting formatted file into chunks of ${split_size} lines..."
split --numeric-suffixes=1 -l "$split_size" "$formatted" "${formatted}."

# ----------------------------
# Run scoring on each split
# ----------------------------
echo "Running labse scoring on each split..."
for split_file in ${formatted}.*; do
    suffix=$(echo "$split_file" | awk -F'.' '{print $NF}')
    output_file="scored.${suffix}.tsv"
    echo "Scoring ${split_file} -> ${output_file}"
    python /gpfs/projects/bsc88/mt_translation/paraclean/scoring/labse_score_store_array-test.py \
        --input "$split_file" \
        --output "$output_file" \
        --l1 $l1 --l2 $l2
done

# ----------------------------
# Merge scored files
# ----------------------------
echo "Merging scored files..."
first_file=$(ls scored.*.tsv | sort | head -n1)
head -n 1 "$first_file" > "$scored"  # header
tail -n +2 -q scored.*.tsv >> "$scored"

# ----------------------------
# Cleanup temporary split files
# ----------------------------
echo "Cleaning up temporary files..."
rm ${formatted}.*
rm scored.*.tsv
echo "Final scored file: ${scored}"

# ----------------------------
# Sampling
# ----------------------------
echo "Sampling based on predefined thresholds..."
python /gpfs/projects/bsc88/mt_translation/paraclean/sampling/sampler.py \
    "$scored" \
    --threshold ${threshold} \
    --l1_probability ${l1_probability} \
    --l2_probability ${l2_probability} \
    --l1 ${l1} \
    --l2 ${l2} \
    --sample_output_path /gpfs/projects/bsc88/mt_translation/paraclean/testing

echo "Pipeline completed successfully."
