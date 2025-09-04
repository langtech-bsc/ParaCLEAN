#!/bin/bash

#SBATCH --job-name=filter
#SBATCH --output=slurm_logs/filter_%j.out
#SBATCH --error=slurm_logs/filter_%j.err
#SBATCH --gres=gpu:1
#SBATCH --time=48:00:00
#SBATCH --cpus-per-task=20
#SBATCH --qos acc_bscls
#SBATCH -N1
#SBATCH --account bsc88
##SBATCH --qos=acc_bscls

SCRIPT_DIR=$(dirname "$0")
ROOT=$(realpath "$SCRIPT_DIR/..")

source "$ROOT/use_env_pipeline.sh"

umask 007

### THIS SCRIPT NEEDS UPDATING ###

#Add all corpora to be sampled to this array
declare -a corpora=(
    "dgt_es-bg_20240605"
    "elrc-emea_es-bg_20240605"
    "globalvoices_es-bg_20240605"
    "kde4_es-bg_20240605"
    "multiccaligned_es-bg_20240605"
    "multiparacrawl_es-bg_20240605"
    "nllb_es-bg_20240605"
    "nteu-pangeanic_es-bg_20240605"
    "nteu-tier3_es-bg_20240605"
    "opensubtitles_es-bg_20240605"
    "tildemodel_es-bg_20240605"
    "wikimatrix_es-bg_20240605"  # Add or remove corpora as needed
)

#Update language variables
l1="es"
l2="bg"

#the sample size is an optional variable and can be left empty. This is the sample size BEFORE deduping, so take that into consideration.
sample_size=""

#Update language probability thresholds. For most languages 0.5 is recommended, but for Idiomata Cognitor
#languages it is recommended that you inspect the scored data to determine the most appropriate level. It
#may well be much lower.
l1p="0.5"
l2p="0.5"

#threshold for labse alignment. Default is 0.75 which works for the majority of languages, but for low resource stuff you may
#want to lower the threshold for alignment

threshold="0.75"

#Put the desired output folder
#(the script will create this folderif it does not yet exist)
output="/gpfs/scratch/bsc88/bsc088400/data/es-bg/sampling"
mkdir -p "$output"

#put the folder in 04-mt-samplings where you want to store the sampled corpus 
#(the script will create this folderif it does not yet exist)
storage_dir=""
mkdir -p ${storage_dir}

####YOU SHOULD NOT NEED TO ALTER THE CODE BELOW HERE###

data_path="/gpfs/projects/bsc88/data/03-mt-repository"

args=""
for corpus in "${corpora[@]}"; do
    if [[ -n $corpus ]]; then
        args+=" ${data_path}/${corpus}/${corpus}.scored"
    fi
done

data_path=/gpfs/projects/bsc88/data/03-mt-repository
python ***REMOVED***/sampling/sampler.py ${args} -t ${threshold} -l1p ${l1p} -l2p ${l2p} --sample_size ${sample_size} --l1 ${l1} --l2 ${l2} --sample_output_path ${output}

bifixer ${output}/filtered_corpus.${l1}-${l2} ${output}/bifixed-corpus.${l1}-${l2} ${l1} ${l2} --header --scol ${l1} --tcol ${l2} --aggressive_dedup --ignore_segmentation

python ***REMOVED***/sampling/dedupe_bifixed.py ${output}/bifixed-corpus.${l1}-${l2} ${output}/deduped-corpus.${l1}-${l2}
 
#extract columns from bifixer output and store in separate text files

round_to_million() {
  local num=$1
  local remainder=$(( num % 1000000 ))
  if [ $remainder -ge 500000 ]; then
    local rounded=$(( (num + 1000000 - remainder) / 1000000 ))
  else
    local rounded=$(( (num - remainder) / 1000000 ))
  fi
  echo $rounded
}

line_count=$(wc -l < "${output}/deduped-corpus.${l1}-${l2}")
echo ${line_count}
rounded_count=$(round_to_million $line_count)
echo ${rounded_count}

 awk -F '\t'  '{print $1}' ${output}/deduped-corpus.${l1}-${l2} > ${storage_dir}/${l1}-${l2}_${rounded_count}M.${l1}
 awk -F '\t'  '{print $2}' ${output}/deduped-corpus.${l1}-${l2} > ${storage_dir}/${l1}-${l2}_${rounded_count}M.${l2}

#rm filtered_corpus.${l1}-${l2} bifixed-corpus.${l1}-${l2}
