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



