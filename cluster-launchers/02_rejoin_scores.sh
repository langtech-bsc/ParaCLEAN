#!/bin/bash

#SBATCH --job-name=rejoin_LABSED
#SBATCH --output=slurm_logs/join_%j.out
#SBATCH --error=slurm_logs/join_%j.err
#SBATCH --time=48:00:00
#SBATCH --cpus-per-task=20
#SBATCH --qos gp_bscls
#SBATCH -N1
#SBATCH --account bsc88
##SBATCH --qos=gp_bscls

umask 007

echo ${scored}
echo ${formatted}

head -n 1 ${scored}.01.tsv > ${scored}; tail -n +2 -q ${scored}.*.tsv >> ${scored}

if [[ -n ${scored} && -n ${formatted} ]]; then

	rm ${formatted}*
	rm ${scored}.*.tsv

else
	echo "Either .scored or .formatted is missing"
fi

