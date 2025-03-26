#!/bin/bash

#SBATCH --job-name=chisqr           # Job name
#SBATCH --output=output_%j.txt      # Standard output (%j = job ID)
#SBATCH --error=error_%j.txt        # Standard error file
#SBATCH --partition=general         # Partition/queue name
#SBATCH --nodes=1                   # Number of nodes
#SBATCH --ntasks=1                  # Number of tasks (e.g., MPI ranks)
#SBATCH --cpus-per-task=4           # Number of CPU cores per task (OpenMP threads)
#SBATCH --mem=16G                    # Memory per node
#SBATCH --time=12:00:00             # Time limit hrs:min:sec
#SBATCH --mail-type=END,FAIL        # Send email on job end or fail
#SBATCH --mail-user=ruoyaoni121@gmail.com  # Your email address

csh chi2_range.csh 1 20

