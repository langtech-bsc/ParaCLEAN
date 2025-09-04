#!/bin/bash

#SBATCH --job-name=single_score-launch_%j
#SBATCH --output=slurm_logs/single_score-launch_%j.out
#SBATCH --error=slurm_logs/single_score-launch_%j.err
#SBATCH --gres=gpu:1
#SBATCH --time=48:00:00
#SBATCH --cpus-per-task=20
#SBATCH --qos acc_bscls
#SBATCH -N1
#SBATCH --account bsc88
##SBATCH --qos=acc_bscls


source ***REMOVED***/use_env_pipeline.sh
umask 007

#Update these five variables manually.
#corpus_id is the directory created to store the raw corpus. Format: corpusname_xx-xx_date.
#data_format can be either "tsv", "plain_text", or "tmx". Other formats are not yet supported.
#split_size can be changed depending on your requirements. 
corpus_id=nteu-pangeanic_es-pt_20240411
data_format=tmx
l1=es
l2=pt
split_size=1000000

metadata_path=/gpfs/projects/bsc88/data/02-metadata/${corpus_id}.json

python_output=$(python ***REMOVED***/input_formats.py --metadata ${metadata_path} --input_format ${data_format} --l1 ${l1} --l2 ${l2})

echo "Full Python Output: ${python_output}"

eval "$(echo "${python_output}" | grep -E 'size_sentences=|formatted=|scored=|l1=|l2=')"

export  metadata_path=${metadata_path} size_sentences=${size_sentences} scored=${scored} formatted=${formatted} l1=${l1} l2=${l2}

#you don't need to change anything below here (but you might want to if you want to change slurm variables etc)
if [[ $size_sentences -gt 2000000 ]]; then
    echo "Splitting is required."
    split --numeric-suffixes=1 -l "$split_size"  "${formatted}" "${formatted}".
    
    array_size=$(ls -1 "${formatted}"* | grep -c "${formatted}.[0-9][0-9]$")
    jid1=$(sbatch --array=1-${array_size} --export=metadata_path,l1,l2 --output=slurm_logs/score-${corpus_id}_%a.out --error=slurm_logs/score-${corpus_id}_%a.err ***REMOVED***/cluster-launchers/01_scoring-array.sh)
    echo "jid1 is: ${jid1}"

    jid2=$(sbatch --dependency=afterany:${jid1##* } --export=metadata_path,scored,formatted --output=slurm_logs/rejoin-${corpus_id}_%a.out --error=slurm_logs/rejoin-${corpus_id}_%a.err ***REMOVED***/cluster-launchers/02_rejoin_scores.sh)
    echo "jid2 is: ${jid2}"
else
    echo "No split required."
    array_size=1
    mv ${formatted} ${formatted}.01
    jid1=$(sbatch --array=1-${array_size} --export=metadata_path,l1,l2 --output=slurm_logs/score-${corpus_id}.out --error=slurm_logs/score-${corpus_id}.err ***REMOVED***/cluster-launchers/01_scoring-array.sh)
    echo "jid1 is: ${jid1}"

    jid2=$(sbatch --dependency=afterany:${jid1##* } --export=metadata_path,scored,formatted --output=slurm_logs/rename-${corpus_id}_%a.out --error=slurm_logs/rename-${corpus_id}_%a.err ***REMOVED***/cluster-launchers/02_rejoin_scores.sh)
    echo "jid2 is: ${jid2}"
fi





