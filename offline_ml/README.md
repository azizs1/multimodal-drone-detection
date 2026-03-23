# Offline ML Setup

This offline_ml folder serves as an offline machine learning hub for the multimodal drone detection capstone project. The steps to install a Conda environment below ensure all users/contributors have the same package versions and dependencies.

---

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

This command below allows you to update the environment.yml file if new dependencies are introduced:
```bash
conda env update -f environment.yml --prune
```

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

There are two main datasets that will be used for this project. The two datasets are below:

Zenodo Visual Drone Detection Dataset - Non-Augemented: https://zenodo.org/records/15632958
Zenodo Thermal Drone Detection Dataset - Non-Augemented: https://zenodo.org/records/15633051
Zenodo Thermal Drone Detection Dataset - Augemented: https://zenodo.org/records/15633098
Anti-UAV: https://github.com/ZhaoJ9014/Anti-UAV (Scroll down to Anti-UAV300 Google Drive link and download from there)

The two main datasets used will be denoted as the Zenodo Drone Detection Dataset and the Anti-UAV Dataset. Each link above should be
downloaded and then stored in the datasets folder in the offline_ml directory. These datasets will be gitignored.

All datasets should be stored in the datasets/ directory and should all be at the same level. Keep the original directory structure for each of the datasets for now.

The names of the datasets have been renamed as follows:
* zenodo_visual_no_augmentation
* zenodo_thermal_no_augmentation
* zenodo_thermal_augmented
* anti_uav

These will have to be the names renamed in the datasets directory to use any associated notebooks or code.

# Initial Data Analysis

The data_extraction Jupyter Notebook has initial data analysis on each of the Zenodo datasets, and can be reviewed in VS code or through the jupyter notebook bash command. Make sure you are in the ml_env conda environment to use the notebook effectively, in addition to having the datasets downloaded, however example outputs are preserved.

# Initial Model Training

While there are some preprocessing steps that could be taken, the data is already in a state that can be accepted by YOLOv8, so I conducted an initial benchmark training session on the three different Zenodo sets. Initial model training and evaluation is done in the train.ipynb notebook, and was ran in Google Colab for free access to their T4 GPU. Model outputs are featured in this notebook as an example, but to replicate this output, you can download the notebook and follow instructions there.

In order to keep all code in the repository and limit the use of external tools, the train.ipynb notebook was converted into train.py, and training is now conducted on the VT ARC Cluster. Instructions below serve as a walkthrough to getting this resource set up. To run train.py locally to test it works, you can run this bash command below, however, CPU training would be too time intensive to train each of these models locally. Make sure this command is ran in the offline_ml/src directory.

```bash
python train.py --data ../datasets --epochs 1
```

# ARC Cluster Setup

To be able to run python scripts connected to the rest of the repository but still ran on GPUs, we utilized the GPU power of the Virginia Tech ARC Cluster. The following instructions note how to get started, however, it should be noted that to get started with the ARC Cluster an instructor must create an account to give you access. The following setup is based on our instructor giving us Instructional Allocation to the ARC Cluster.

## 1. Setting up SSH Connection

Once the instructor has given you access, the first step is to ssh into one of the computing resources ARC provides. The easiest way to do this is through VS Code. First, ensure you have the Remote - SSH extension installed and locate the icon on the extension bar on the left titled "Remote Explorer". Click on this and then hover over the SSH dropdown and click the "+" icon on the right. The ssh command entered should look something like this below:

```bash
ssh <your_PID>@tinkercliffs2.arc.vt.edu
```

There are multiple different resources (such as tinkercliffs1 or falcon1, but tinkercliffs had the GPU resources that would work the best for our project). The SSH config file selection should already be created for you and be in your Users directory, so select this one. If this works, you will be asked to enter your Virginia Tech password and then will have to authenticate using DUO mobile on your phone or other device.

This tutorial provides more in-depth instructions: https://video.vt.edu/media/Connect+to+ARC+Systems+with+VSCode/1_5q3mxyi0

## 2. Git Clone Repository

Next, use git to clone this repository onto your ARC account:

```bash
git clone https://github.com/azizs1/multimodal-drone-detection.git
```

This should provide all of the same code that it provides on your local machine, however, now you have the option to run the code on better computing resources.

## 3. Setting up Environment

To set up an environment on the ARC cluster, you have to set it up on the compute node that you want to run the training code on. The following commands allow for quick environment setup.

First, get yur account id you need to run jobs on the ARC cluster, this id will be useful when running jobs later.
```bash

```

Then, start an interactive job on the compute node that training will take place on:
```bash
--partition=a100_normal_q --nodes=1 --ntasks-per-node=4 --gres=gpu:1 --account=<account_id>
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

## 4. Migrate Data to ARC Cluster

NOTE: If you are already a member of the team, skip this step, the datasets are already in our shared projects/muataz folder.

For documentation purposes, this is how I got the datasets into our shared folder on the ARC cluster. These datasets were stored into a project folder provided by our instructor:

```bash
cd /projects/<project_name>
mkdir datasets
cd datasets
wget "https://zenodo.org/records/15632958/files/Visual%20drone%20detection.v2i.yolov11_no_augmentation.zip?download=1" -O zenodo_visual_no_augmentation.zip
wget "https://zenodo.org/records/15633051/files/Thermal_drone_detection.v1i.yolov11_no_augmentation.zip?download=1" -O zenodo_thermal_no_augmentation.zip
wget "https://zenodo.org/records/15633098/files/Thermal_drone_detection.v4i.yolov11.zip?download=1" -O zenodo_thermal_augmented.zip
unzip zenodo_visual_no_augmentation.zip -d zenodo_visual_no_augmentation
unzip zenodo_thermal_no_augmentation.zip -d zenodo_thermal_no_augmentation
unzip zenodo_thermal_augmented.zip -d zenodo_thermal_augmented
rm zenodo_visual_no_augmentation.zip
rm zenodo_thermal_no_augmentation.zip
rm zenodo_thermal_augmented.zip
```

## 5. Creating a SLURM Job