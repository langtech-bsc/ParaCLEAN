#!/bin/bash

#SBATCH --job-name=sample-mt-pipe
#SBATCH --output=slurm_logs/sample-mt-pipe_%j.out
#SBATCH --error=slurm_logs/sample-mt-pipe_%j.err
#SBATCH --gres=gpu:1
#SBATCH --time=2:00:00
#SBATCH --cpus-per-task=20
#SBATCH --qos acc_debug
#SBATCH -N1
#SBATCH --account bsc88
##SBATCH --qos=acc_debug

source /gpfs/scratch/bsc88/bsc088400/vecalign_experiments/vecalign-venv/bin/activate

umask 007


rootdir='/gpfs/scratch/bsc88/bsc088400/vecalign_experiments'

vecalign="/gpfs/scratch/bsc88/bsc088400/vecalign_experiments/vecalign"


labse-embed() {
     in_file=$1
     out_file=$2
     python /gpfs/scratch/bsc88/bsc088400/vecalign_experiments/vecalign-labse/src/embed.py \
                --input  $in_file \
                --output  $out_file \

}


for file in $rootdir/* ; do

    if [[ $file == *ca ]]; then
        src=$file
    elif [[ $file == *es ]]; then
        tgt=$file
    fi
done

if [[ -n $src && -n $tgt ]]; then
    d=$(dirname "$src") 
    echo 
    tmp_dir="${d}/tmp"
    out="${d}/align"
    echo $out

    # rm -rf $tmp_dir
    # mkdir -p $tmp_dir
        
    # ${vecalign}/overlap.py -i $src -o $d/tmp/overlaps.es -n 3
    # ${vecalign}/overlap.py -i $tgt -o $d/tmp/overlaps.ca -n 3
    # echo "Overlap.py run"
        
    labse-embed $d/tmp/overlaps.es  $d/tmp/overlaps.es.emb
    labse-embed $d/tmp/overlaps.ca  $d/tmp/overlaps.ca.emb
        
    echo "LABSE embeddings calculated"

    # ${vecalign}/vecalign.py --alignment_max_size 3 --src $src --tgt $tgt --src_embed $d/tmp/overlaps.es $d/tmp/overlaps.es.emb --tgt_embed $d/tmp/overlaps.ca $d/tmp/overlaps.ca.emb > $d/tmp/vecalign_alignments.log
    # echo "vecalign run"

    # python3 vecalign-labse/src/02_vecaligner.py $d/tmp/vecalign_alignments.log $src $tgt $out
    # echo "alignments processed"
else
    echo "Either source or target file is missing in $rootdir"
fi
