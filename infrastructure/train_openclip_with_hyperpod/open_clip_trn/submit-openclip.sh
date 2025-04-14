#!/bin/bash
#SBATCH -N 2
#SBATCH --exclusive
#SBATCH -o openclip.out

export OMP_NUM_THREADS=1

srun only_compile_dis.sh
