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
You should see "(ml_env)" to the left of your username. If this appears, you're Conda environment will be setup and you will now be able to run code within this folder.

## 3. Additional Information

This command below allows you to update the environment.yml file if new dependencies are introduced:
```bash
conda env update -f environment.yml --prune
```

This command allows you to update the environment.yml file if new packages are installed or removed:
```bash
conda env export > environment.yml
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


