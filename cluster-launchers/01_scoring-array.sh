#!/bin/bash

#SBATCH --job-name=score-pipe
#SBATCH --output=slurm_logs/score-pipe_%j.out
#SBATCH --error=slurm_logs/score-pipe-_%j.err
#SBATCH --time=8:00:00
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=20
#SBATCH --qos acc_bscls
#SBATCH -N1
#SBATCH --account bsc88
##SBATCH --qos=acc_bscls

SCRIPT_DIR=$(dirname "$0")
ROOT=$(realpath "$SCRIPT_DIR/..")

source "$ROOT/use_env_pipeline.sh"

umask 007

python ***REMOVED***/scoring/labse_score_store_array-test.py \
    --input ${formatted}.$(printf "%02d" ${SLURM_ARRAY_TASK_ID}) \
    --output ${scored}.$(printf "%02d" ${SLURM_ARRAY_TASK_ID}).tsv \
    --split ${SLURM_ARRAY_TASK_ID} \
    --l1 ${l1} \
    --l2 ${l2}

#python ***REMOVED***/scoring/labse_score_store_array-test.py --metadata ${metadata_path} --split ${SLURM_ARRAY_TASK_ID} --l1 ${l1} --l2 ${l2}
