#!/bin/bash

#SBATCH --job-name=score-launch_%j
#SBATCH --output=slurm_logs/score-launch_%j.out
#SBATCH --error=slurm_logs/score-launch_%j.err
#SBATCH --gres=gpu:1
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=20
#SBATCH --qos acc_debug
#SBATCH -N1
#SBATCH --account bsc88
##SBATCH --qos=acc_debug

SCRIPT_DIR=$(dirname "$0")
ROOT=$(realpath "$SCRIPT_DIR/..")

source "$ROOT/use_env_pipeline.sh"

umask 007

# Declare corpora to be scored
declare -a corpora=(
    multiccaligned-full_ca-ja_20250904
)

# Set other variables
data_format=plain_text # can be either "tsv", "plain_text", or "raw_csv"
l1=ca
l2=ja
split_size=1000000


for corpus_id in "${corpora[@]}"; do

    echo "Processing corpus: ${corpus_id}"

    corpus_dir=/gpfs/projects/bsc88/mt_translation/paraclean/data/raw-corpora/${corpus_id}

    # autodetect language files
    l1_file=$(find "${corpus_dir}" -maxdepth 1 -type f -name "*.${l1}" | head -n1)
    l2_file=$(find "${corpus_dir}" -maxdepth 1 -type f -name "*.${l2}" | head -n1)

    if [[ -z "$l1_file" || -z "$l2_file" ]]; then
        echo "Could not find both language files for ${corpus_id} (l1=${l1}, l2=${l2})"
        continue
    fi

    python_output=$(python /gpfs/projects/bsc88/mt_translation/paraclean/input_formats.py \
    --input ${l1_file} ${l2_file} \
    --input_format ${data_format} \
    --l1 ${l1} --l2 ${l2} \
    --format /gpfs/projects/bsc88/mt_translation/paraclean/data/scored/output_file.formatted.tsv \
    --output /gpfs/projects/bsc88/mt_translation/paraclean/data/scored/output_file.scored)

    echo "Full Python Output: ${python_output}"

    eval "$(echo "${python_output}" | grep -E 'size_sentences=|formatted=|scored=|l1=|l2=')"

    export size_sentences=${size_sentences} scored=${scored} formatted=${formatted} l1=${l1} l2=${l2}

    #Check if splitting is required
    if [[ $size_sentences -gt 1000000 ]]; then
        echo "Splitting is required."
        
        split --numeric-suffixes=1 -l "$split_size"  "${formatted}" "${formatted}".
        
        array_size=$(ls -1 "${formatted}"* | grep -c "${formatted}.[0-9][0-9]$")
        jid1=$(sbatch --array=1-${array_size} \
            --export=l1,l2,formatted \
            --output=slurm_logs/score-${!corpus_id}_%a.out \
            --error=slurm_logs/score-${!corpus_id}_%a.err \
            /gpfs/projects/bsc88/mt_translation/paraclean/cluster-launchers/01_scoring-array.sh)
        echo "jid1 is: ${jid1}"

        jid2=$(sbatch --dependency=afterany:${jid1##* } \
            --export=scored,formatted \
            --output=slurm_logs/rejoin-${!corpus_id}.out \
            --error=slurm_logs/rejoin-${!corpus_id}.err \
            /gpfs/projects/bsc88/mt_translation/paraclean/cluster-launchers/02_rejoin_scores.sh)
        echo "jid2 is: ${jid2}"

    else
        echo "No split required."
        array_size=1
        mv ${formatted} ${formatted}.01
        jid1=$(sbatch --array=1-${array_size} \
            --export=l1,l2,formatted \
            --output=slurm_logs/score-${!corpus_id}.out \
            --error=slurm_logs/score-${!corpus_id}.err \
            /gpfs/projects/bsc88/mt_translation/paraclean/cluster-launchers/01_scoring-array.sh)
        echo "jid1 is: ${jid1}"

        jid2=$(sbatch --dependency=afterany:${jid1##* } \
            --export=scored,formatted \
            --output=slurm_logs/rejoin-${!corpus_id}.out \
            --error=slurm_logs/rejoin-${!corpus_id}.err \
            /gpfs/projects/bsc88/mt_translation/paraclean/cluster-launchers/02_rejoin_scores.sh)
        echo "jid2 is: ${jid2}"
    fi

done




