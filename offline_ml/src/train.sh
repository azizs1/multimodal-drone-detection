#!/bin/bash
#SBATCH --job-name=mdd_offline_ml_training

#NOTE: ADD IN YOUR ACCOUNT ID HERE:
#SBATCH --account=lnn

#General node to run on and time allocated.
#SBATCH --partition=a100_normal_q
#SBATCH --time=12:00:00

#Specific compute resources.
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1

#Where to store output (NOTE: ADD PID HERE).
#SBATCH --output=/scratch/eymauger26/logs/mdd_offline_ml_training.%j.out
#SBATCH --error=/scratch/eymauger26/logs/mdd_offline_ml_training.%j.err

# Reset modules.
module reset

# Load Conda environment.
module load Miniforge3
source activate /home/eymauger26/envs/ml_env #UPDATE PID HERE.

# Copy and unzip datasets to local NVMe for fast I/O during training.
cp /projects/muataz/datasets/*.zip $TMPDIR #UPDATE PROJECT NAME HERE IF NECESSARY.
cd $TMPDIR
unzip zenodo_visual_no_augmentation.zip
unzip zenodo_thermal_no_augmentation.zip
unzip zenodo_thermal_augmented.zip

# Run the train.py script with the local data (UPDATE PID HERE).
cd ~/multimodal-drone-detection
python offline_ml/src/train.py \
    --data $TMPDIR \
    --project /scratch/eymauger26/runs \
    --epochs 50