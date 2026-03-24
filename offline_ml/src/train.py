import argparse
from pathlib import Path
from ultralytics import YOLO

#Define arguments to pass into the model. This allows the code to be used locally or on ARC, and only changes the command entered by the user.
def parse_args():
    parser = argparse.ArgumentParser(description="Train YOLO models for drone detection")
    parser.add_argument("--data", type=str, required=True, help="Path to datasets directory")
    parser.add_argument("--project", type=str, default="../runs", help="Path to save training outputs")
    parser.add_argument("--model", type=str, default="../weights/yolov8n.pt", help="YOLO model size")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    return parser.parse_args()

#Condensed training loop that works for each dataset, assuming the directory structures are all the same.
def train(args):
    #Get the data and project directories.
    data_dir = Path(args.data).resolve()
    project_dir = Path(args.project).resolve()

    #Save specific datasets that should all be trained with YOLOv8. These can be changed in the future, but the train.py code will have to be modified.
    datasets = [
        {
            "data": data_dir / "zenodo_visual_no_augmentation/data.yaml",
            "name": "visual_no_augmentation_baseline"
        },
        {
            "data": data_dir / "zenodo_thermal_no_augmentation/data.yaml",
            "name": "thermal_no_augmentation_baseline"
        },
        {
            "data": data_dir / "zenodo_thermal_augmented/data.yaml",
            "name": "thermal_augmented_baseline"
        },
    ]

    #Simple training loop for each dataset.
    for dataset in datasets:
        print("---------------------------------------")
        print(f"Training {dataset['name']}")
        print("---------------------------------------\n")

        # Loads the model (options include yolov8n.pt (smallest), yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt)
        model = YOLO(args.model)

        #Train the dataset, looking at specific arguments.
        result = model.train(
            exist_ok=True,
            data=str(dataset["data"]),
            project=str(project_dir),
            name=dataset["name"],
            epochs=args.epochs
        )

        print("---------------------------------------")
        print(f"\nEvaluating {dataset['name']}")
        print("---------------------------------------\n")

        #Evaluate the best model performance for each dataset on the test set of that dataset.
        model = YOLO(str(Path(result.save_dir) / "weights/best.pt"))
        model.val(
            exist_ok=True,
            split="test", 
            plots=True,
            data=str(dataset["data"]), 
            project=str(project_dir),
            name=dataset["name"] + "_val"
        )

if __name__ == "__main__":
    args = parse_args()
    train(args)