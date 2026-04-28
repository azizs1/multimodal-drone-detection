#!/bin/bash
#SBATCH --job-name=mdd_offline_ml_training

#NOTE: ADD IN YOUR ACCOUNT ID HERE:
#SBATCH --account=lnn

#General node to run on and time allocated.
#SBATCH --partition=h200_normal_q
#SBATCH --time=12:00:00

#Specific compute resources.
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
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
unzip -q zenodo_visual_no_augmentation.zip
unzip -q zenodo_thermal_no_augmentation.zip
unzip -q anti_uav_visual_no_augmentation.zip
unzip -q anti_uav_thermal_no_augmentation.zip
unzip -q halmstad_visual_no_augmentation.zip
unzip -q halmstad_thermal_no_augmentation.zip

# Run the train.py script with the local data (UPDATE PID HERE).
cd ~/multimodal-drone-detection
python offline_ml/src/train.py \
    --data $TMPDIR \
    --project /scratch/eymauger26/runs \
    --epochs 50

# Add the updated weights to the weights directory to be committed.
cp /scratch/eymauger26/runs/zenodo_visual_baseline/weights/best.pt ~/multimodal-drone-detection/offline_ml/weights/zenodo_visual_best.pt
cp /scratch/eymauger26/runs/zenodo_thermal_baseline/weights/best.pt ~/multimodal-drone-detection/offline_ml/weights/zenodo_thermal_best.pt
cp /scratch/eymauger26/runs/anti_uav_visual_baseline/weights/best.pt ~/multimodal-drone-detection/offline_ml/weights/anti_uav_visual_best.pt
cp /scratch/eymauger26/runs/anti_uav_thermal_baseline/weights/best.pt ~/multimodal-drone-detection/offline_ml/weights/anti_uav_thermal_best.pt
cp /scratch/eymauger26/runs/halmstad_visual_baseline/weights/best.pt ~/multimodal-drone-detection/offline_ml/weights/halmstad_visual_best.pt
cp /scratch/eymauger26/runs/halmstad_thermal_baseline/weights/best.pt ~/multimodal-drone-detection/offline_ml/weights/halmstad_thermal_best.pt