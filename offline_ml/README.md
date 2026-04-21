# Offline ML Setup

This offline_ml folder serves as an offline machine learning section of the repo for the multimodal drone detection capstone project. The steps to install a Conda environment below ensure all users/contributors have the same package versions and dependencies.

## 1. Prerequisites

Before setting up the environment, make sure you have one of the following installed:
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) (recommended)
- [Anaconda](https://www.anaconda.com/download)

Check installation with the command below:
```bash
conda --version
```
If this command returns with a version number, your conda is correctly installed.

## 2. Create Environment

Follow the commands below to create a Conda environment. Make sure you are currently in the offline_ml directory.
```bash
conda env create -f environment.yml
conda activate ml_env
```
You should see "(ml_env)" to the left of your username. If this appears, you're Conda environment will be setup and you will now be able to run code within this folder. In addition, check the bottom right of your VS code to see the python version you are running. It should be "ml_env (3.12.3)". If it is something else, make sure your environment is activated and make sure the Python venv called multimodal-drone-detection is not active. This is a venv that is used for backend and other parts of the code base. The command below will remove the venv from your terminal, but you still need to ensure that the correct environment is being used in the bottom left.

```bash
deactivate
```

## 3. Additional Information

This command allows you to update the environment.yml file if new packages are installed or removed:
```bash
conda env export > environment.yml
```

## 4. Linting

For any linting needs, ruff and uv are present in the conda environment to help format files correctly and determine/fix linting errors. The following commands can be run to help with linting.

For changing the linting format of the full file (DO THIS FIRST).
```bash
uv run ruff format <file_path>
```

For basic checking and fixing of linting errors.
```bash
ruff check --fix
```


# Datasets

The following datasets are used for this project. All datasets should be stored in the `datasets/` directory at the same level with the directory names listed below.

## 1. Zenodo Datasets

- [Zenodo Visual Drone Detection Dataset - Non-Augmented](https://zenodo.org/records/15632958) — `zenodo_visual_no_augmentation`
- [Zenodo Thermal Drone Detection Dataset - Non-Augmented](https://zenodo.org/records/15633051) — `zenodo_thermal_no_augmentation`

## 2. Anti-UAV Dataset

- [Anti-UAV](https://github.com/ZhaoJ9014/Anti-UAV) — Paired RGB and thermal infrared video sequences of drones in the wild. Download and place the raw dataset at `datasets/anti_uav`. Run the preprocessing script (see Preprocessing section) to generate the processed datasets:
  - `anti_uav_visual_no_augmentation`
  - `anti_uav_thermal_no_augmentation`


# Initial Data Analysis

The `data_exploration` Jupyter Notebook has initial data analysis on each dataset and can be reviewed in VS Code or through the jupyter notebook bash command. Make sure you are in the ml_env conda environment to use the notebook effectively, in addition to having the datasets downloaded. Example outputs are preserved in the notebook.


# Preprocessing

All preprocessing scripts should be run from the `offline_ml/` directory.

## 1. Zenodo Thermal Dataset

The thermal dataset contained ~18% of images with empty label files across train, valid, and test splits. These images and their empty label files are removed from the dataset by running:

```bash
python src/preprocessing_zenodo.py
```

This script moves all images with empty label files to a temporary directory and then deletes it, leaving only fully labeled images in the dataset.

## 2. Anti-UAV Dataset

The Anti-UAV dataset consists of paired infrared and visible video sequences with JSON annotations. The preprocessing script extracts frames from each video, converts bounding box annotations from pixel coordinates to YOLO format, and outputs two processed datasets — one thermal and one visual — matching the zenodo directory structure.

Key preprocessing decisions:
- Frames are sampled at every 10th frame to avoid near-duplicate frames while preserving drone motion diversity
- All frames where the drone is not present (exist=0 in JSON) are kept regardless of sample rate as hard negative examples
- Infrared sequences are output to `anti_uav_thermal_no_augmentation`, visible to `anti_uav_visual_no_augmentation`
- The Anti-UAV `val` split is renamed to `valid` to match zenodo structure

Run the preprocessing script:
```bash
python src/preprocessing_anti_uav.py
```

Note: Visual has significantly more negative frames (~37%) than thermal (~11%). This could be due to the fact that humans were not able to identify drones when looking at the pictures to label them. This is expected behavior and reflects real-world sensor differences, showing the importance of thermal imagery at night.


# Initial Model Training

While there are some preprocessing steps that could be taken, the data is already in a state that can be accepted by YOLO, so I conducted an initial benchmark training session on the two different Zenodo sets. Initial model training and evaluation is done in the train.ipynb notebook, and was ran in Google Colab for free access to their T4 GPU. Model outputs are featured in this notebook as an example, but to replicate this output, you can download the notebook and follow instructions there.

In order to keep all code in the repository and limit the use of external tools, the train.ipynb notebook was converted into train.py, and training is now conducted on the VT ARC Cluster. Instructions below serve as a walkthrough to getting this resource set up. To run train.py locally to test it works, you can run this bash command below, however, CPU training would be too time intensive to train each of these models locally. Make sure this command is ran in the offline_ml/src directory.

```bash
python train.py --data ../datasets --epochs 1
```

# Model Robustness

To improve model robustness beyond the initial Zenodo baselines, additional datasets have been integrated to address key gaps identified during data analysis:

- **Limited drone diversity** — only 3 drone types in Zenodo
- **No hard negatives** — model had never seen images without drones
- **Limited range** — most Zenodo drones are within 100m
- **No nighttime data**

## Datasets Added

**Anti-UAV** — 296,901 frames of paired RGB and thermal drone footage across 320 sequences. Provides small bounding boxes (long range drones), nighttime footage, and hard negative examples. Preprocessed using `src/preprocessing_anti_uav.py`.

## Planned Datasets

The following datasets are pending access approval:
- **WOSDETC Drone-vs-Bird** — ground camera video, drone and bird annotations, email request to wosdetc@googlegroups.com
- **LRDDv2** — long range drone detection up to 1km, access request at research.coe.drexel.edu/ece/imaple/lrddv2
- **FBD-SV-2024** — flying bird surveillance video, available at github.com/Ziwei89/FBD-SV-2024_github
- **Halmstad Multi-Sensor** — drone/bird/plane/helicopter, available at github.com/DroneDetectionThesis/Drone-detection-dataset (requires MATLAB for annotation extraction)

## Training Strategy

Each dataset is trained independently first to establish baselines before combining. This allows direct comparison of what each dataset contributes to model performance. Training is configured in `src/train.py` with the following baselines:

- `zenodo_visual_baseline`
- `zenodo_thermal_baseline`
- `anti_uav_visual_baseline`
- `anti_uav_thermal_baseline`


# ARC Cluster Setup

To be able to run python scripts connected to the rest of the repository but still ran on GPUs, we utilized the GPU power of the Virginia Tech ARC Cluster. The following instructions note how to get started, however, it should be noted that to get started with the ARC Cluster an instructor must create an account to give you access. The following setup is based on our instructor giving us Instructional Allocation to the ARC Cluster.

## 1. Setting up VPN

To be able to access the ARC cluster when you are at home or not on eduroam wifi, you must use a VPN. To access the VPN, please follow the instructions for your specific configuration using this [link](https://www.nis.vt.edu/ServicePortfolio/Network/RemoteAccess-VPN.html).

## 2. Setting up SSH Connection

Once the instructor has given you access, the first step is to ssh into one of the computing resources ARC provides. The easiest way to do this is through VS Code. First, ensure you have the Remote - SSH extension installed and locate the icon on the extension bar on the left titled "Remote Explorer". Click on this and then hover over the SSH dropdown and click the "+" icon on the right. The ssh command entered should look something like this below:

```bash
ssh <your_PID>@tinkercliffs2.arc.vt.edu
```

There are multiple different resources (such as tinkercliffs1 or falcon1, but tinkercliffs had the GPU resources that would work the best for our project). The SSH config file selection should already be created for you and be in your Users directory, so select this one. If this works, you will be asked to enter your Virginia Tech password and then will have to authenticate using DUO mobile on your phone or other device.

This [tutorial](https://video.vt.edu/media/Connect+to+ARC+Systems+with+VSCode/1_5q3mxyi0) provides more in-depth instructions.

## 3. Git Clone Repository

Next, use git to clone this repository onto your ARC account:

```bash
git clone https://github.com/azizs1/multimodal-drone-detection.git
```

This should provide all of the same code that it provides on your local machine, however, now you have the option to run the code on better computing resources.

## 4. Setting up Environment

To set up an environment on the ARC cluster, you have to set it up on the compute node that you want to run the training code on. The following commands allow for quick environment setup. This environment only needs to be created once in the partition that you will use, and then will be able to be activated during other training jobs on the same partition.

First, get your account id you need to run jobs on the ARC cluster, this id will be useful when running jobs later. There will potentially be multiple account ids that show up, including "personal". Use the one that doesn't say "personal", mine is "lnn"
```bash
sacctmgr show associations user=$USER format=account
```

Then, start an interactive job on the compute node that training will take place on:
```bash
interact --partition=a100_normal_q --nodes=1 --ntasks-per-node=4 --gres=gpu:1 --account=<account_id>
```

If you see text like similar to the text below, then it mean you are successfully on a compute node and can continue:

 *--- Warning:*
     *Your session consumes resources (CPUs, memory, and GPUs) while it remains open.*
     *Close your session whenever you finish your work.*
     *Other users cannot use the resources allocated to your job until you close your session.*
     *Consider the use of batch jobs to optimize resources allocation.*
*srun: job 4843586 queued and waiting for resources*
*srun: job 4843586 has been allocated resources*
*[eymauger26@tc-dgx008 multimodal-drone-detection]$*

Load Miniforge onto the compute node:
```bash
module load Miniforge3
```

Make sure you are in the multimodal-drone-detection directory (root directory of the repo) and then run the command below:
```bash
conda env create -p ~/envs/ml_env -f offline_ml/environment.yml
```

It will take quite a while to load the environment onto the node. Once it is good to go, activate it.
```bash
source activate /home/<PID>/envs/ml_env
python offline_ml/src/train.py --data offline_ml/datasets --epochs 1
```

The compute node may be slow, so as long as that second command runs the environment should be good to go. Exit out of the interactive node.
```bash
exit
```

## 5. Migrate Data to ARC Cluster

NOTE: If you are already a member of the team, skip this step, the datasets are already in our shared projects/muataz/datasets folder.

For documentation purposes, this is how I got the datasets into our shared folder on the ARC cluster. These datasets are stored as zip files and during training they are unzipped locally for better performance. These datasets were stored into a project folder provided by our instructor. To get the datasets onto ARC, preprocess them locally first from the `datasets/` dir and then upload the processed zip files to the projects folder:
```bash
zip -r zenodo_thermal_no_augmentation.zip zenodo_thermal_no_augmentation
zip -r zenodo_visual_no_augmentation.zip zenodo_visual_no_augmentation
zip -r anti_uav_thermal_no_augmentation.zip anti_uav_thermal_no_augmentation
zip -r anti_uav_visual_no_augmentation.zip anti_uav_visual_no_augmentation
```

## 6. Creating and Submitting a SLURM Job

Now, to run code on the ARC cluster, you have to create jobs using a bash script. The following section outlines how to set this up.

First, create a scratch directory to store your training outputs:
```bash
mkdir -p /scratch/<PID>
```

Next, you have to update the script to add in your own credentials so that it works. The SLURM job script is located at `offline_ml/src/train.sh`. Before submitting, make sure to update the following in the script:
- `--account=<account_id>` — your account ID from step 4
- `--output` and `--error` paths — replace `eymauger26` with your PID
- `source activate` path — replace `eymauger26` with your PID
- `/projects/muataz/datasets` — update if the project folder name changes

Once you are ready, make sure you are located in the root directory of the repo and run this bash command to submit the job:
```bash
sbatch offline_ml/src/train.sh
```

To monitor that the job is running, run this command below:
```bash
squeue -u $USER
```

The status column will show the status of the job. These are the common values and what they mean.
- `PD` — job is pending/waiting for resources
- `R` — job is running
- `CG` — job is completing

To cancel a job that you didn't mean to queue, you can run this command below.
```bash
scancel <jobid>
```

Training logs are saved to `/scratch/<PID>/logs` as `.out` and `.err` files. The `.out` file contains the training progress output and the `.err` file contains any errors. To check the output logs, run this command below:
```bash
cat /scratch/<PID>/logs/mdd_offline_ml_training.<jobid>.out
```

To check the error logs, run this command below:
```bash
cat /scratch/<PID>/logs/mdd_offline_ml_training.<jobid>.err
```

If you want to watch the output in real time while the job is running:
```bash
tail -f /scratch/<PID>/logs/mdd_offline_ml_training.<jobid>.out
```

Once the job finishes, results will be saved to `/scratch/<PID>/runs/`. To find your trained model weights:
```bash
find /scratch/<PID>/runs -name "best.pt"
```

The slurm script automatically saves these weights into the weights directory and can then be commited to git or removed.

<!-- 

#NOTES

Fix yolo26n problem and make it modularizable if I want to to look at other models to use

To prevent the script from downloading the same model every time, a base yolo model has been downloaded in the offline_ml/weights directory. train.py points to this model, and if additional types of yolo models want to be used for training they can be downloaded using the commands below:
```bash
cd ~/multimodal-drone-detection
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" 
mv yolov8n.pt offline_ml/weights/
```

Additional types of YOLO models include yolov8s.pt, yolov8m.pt, yolov8l.pt, and yolov8x.pt.

-->