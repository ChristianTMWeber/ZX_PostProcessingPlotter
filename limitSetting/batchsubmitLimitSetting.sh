#!/bin/bash

# submit to batch via: sbatch <script>


# settings for the batch system:
#SBATCH --job-name=mc16aToys
#SBATCH --ntasks=1 --nodes=1
#SBATCH --mem-per-cpu=5G
#SBATCH --time=12:00:00
#SBATCH --array=4-104


python limitSetting.py --outputDir mc16aToys --outputFileName $SLURM_ARRAY_TASK_ID 
