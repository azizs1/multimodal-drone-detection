import os
from pathlib import Path
from ultralytics import YOLO

#Configure weights, data, and output directories.
WEIGHTS_PATH = Path("weights")
DATASETS_PATH = Path("/localscratch-nvme/5232701")
PROJECT_PATH = Path("runs/cross_evaluation")

#Evaluate each weight in the weights directory on the datasets in the datasets that match the weight's modality.
def evaluate():
    #Make the projects directory if it doesn't exist.
    PROJECT_PATH.mkdir(parents=True, exist_ok=True)

    #Get all weights and datasets.
    weights = list(WEIGHTS_PATH.glob("*.pt"))
    print(weights)
    datasets = [dataset for dataset in DATASETS_PATH.iterdir() if dataset.is_dir()]

    #Separate by modality.
    visual_weights = [weight for weight in weights if "visual" in weight.name]
    thermal_weights = [weight for weight in weights if "thermal" in weight.name]
    visual_datasets = [dataset for dataset in datasets if "visual" in dataset.name]
    thermal_datasets = [dataset for dataset in datasets if "thermal" in dataset.name]

    #Evaluate visual weights.
    print("\n-- Visual --------------------------")
    for weight_path in visual_weights:
        #Create the model.
        model = YOLO(str(weight_path))
        model_name = weight_path.stem

        #Loop through the visual datasets.
        for dataset_path in visual_datasets:
                yaml_path = dataset_path / "data.yaml"
                
                #Name the evaluation based on the combinaton.
                eval_name = f"{model_name}_on_{dataset_path.name}"
                print("---------------------------------------")
                print(f"Evaluating {eval_name}")
                print("---------------------------------------\n")

                #Evaluate the model
                model.val(
                    data=str(yaml_path.resolve()),
                    split="test",
                    plots=True,
                    project=str(PROJECT_PATH.resolve()),
                    name=eval_name,
                    exist_ok=True,
                )
    
    #Evaluate thermal weights.
    print("\n-- Thermal --------------------------")
    for weight_path in thermal_weights:
        #Create the model.
        model = YOLO(str(weight_path))
        model_name = weight_path.stem

        #Loop through the thermal datasets.
        for dataset_path in thermal_datasets:
                yaml_path = dataset_path / "data.yaml"
                
                #Name the evaluation based on the combinaton.
                eval_name = f"{model_name}_on_{dataset_path.name}"
                print("---------------------------------------")
                print(f"Evaluating {eval_name}")
                print("---------------------------------------\n")

                #Evaluate the model.
                model.val(
                    exist_ok=True,
                    split="test",
                    plots=True,
                    data=str(yaml_path.resolve()),
                    project=str(PROJECT_PATH.resolve()),
                    name=eval_name,
                )

if __name__ == "__main__":
    evaluate()