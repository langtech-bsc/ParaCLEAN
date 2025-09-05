#!/bin/bash

#SBATCH --job-name=unit-test
#SBATCH --output=slurm_logs_ella/unit-test_%j.out
#SBATCH --error=slurm_logs_ella/unit-test_%j.err
#SBATCH --time=0:15:00
#SBATCH --cpus-per-task=20
#SBATCH --qos gp_debug
#SBATCH -N1
#SBATCH --account bsc88
##SBATCH --qos=gp_debug


module load anaconda
source /gpfs/scratch/bsc88/bsc088400/venvs/norm_venv_20250818/bin/activate
umask 007
python unit_testing.py
