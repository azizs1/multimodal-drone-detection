#!/bin/bash
#SBATCH --job-name=mdd_combined_training

#NOTE: ADD IN YOUR ACCOUNT ID HERE:
#SBATCH --account=lnn

#General node to run on and time allocated.
#SBATCH --partition=a100_normal_q
#SBATCH --time=55:00:00

#Specific compute resources.
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1

#Where to store output (NOTE: ADD PID HERE).
#SBATCH --output=/scratch/eymauger26/logs/mdd_combined_training.%j.out
#SBATCH --error=/scratch/eymauger26/logs/mdd_combined_training.%j.err

# Reset modules.
module reset

# Load Conda environment.
module load Miniforge3
source activate /home/eymauger26/envs/ml_env

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
python offline_ml/src/train_combined.py \
    --data $TMPDIR \
    --project /scratch/eymauger26/runs \
    --epochs 50

# Add the updated weights to the weights directory to be committed.
# cp /scratch/eymauger26/runs/visual_zenodo_antiuav/weights/best.pt ~/multimodal-drone-detection/offline_ml/weights/visual_zenodo_antiuav_best.pt
# cp /scratch/eymauger26/runs/visual_zenodo_halmstad/weights/best.pt ~/multimodal-drone-detection/offline_ml/weights/visual_zenodo_halmstad_best.pt
# cp /scratch/eymauger26/runs/visual_antiuav_halmstad/weights/best.pt ~/multimodal-drone-detection/offline_ml/weights/visual_antiuav_halmstad_best.pt
# cp /scratch/eymauger26/runs/visual_all/weights/best.pt ~/multimodal-drone-detection/offline_ml/weights/visual_all_best.pt
# cp /scratch/eymauger26/runs/visual_all_weighted/weights/best.pt ~/multimodal-drone-detection/offline_ml/weights/visual_all_weighted_best.pt
# cp /scratch/eymauger26/runs/thermal_zenodo_antiuav/weights/best.pt ~/multimodal-drone-detection/offline_ml/weights/thermal_zenodo_antiuav_best.pt
# cp /scratch/eymauger26/runs/thermal_zenodo_halmstad/weights/best.pt ~/multimodal-drone-detection/offline_ml/weights/thermal_zenodo_halmstad_best.pt
# cp /scratch/eymauger26/runs/thermal_antiuav_halmstad/weights/best.pt ~/multimodal-drone-detection/offline_ml/weights/thermal_antiuav_halmstad_best.pt
# cp /scratch/eymauger26/runs/thermal_all/weights/best.pt ~/multimodal-drone-detection/offline_ml/weights/thermal_all_best.pt
cp /scratch/eymauger26/runs/thermal_all_weighted/weights/best.pt ~/multimodal-drone-detection/offline_ml/weights/thermal_all_weighted_best.pt