import argparse
from pathlib import Path

from ultralytics import YOLO


# Define arguments to pass into the model. This allows the code to be used locally or on ARC,
# and only changes the command entered by the user.
def parse_args():
    parser = argparse.ArgumentParser(description="Combined dataset training for drone detection")
    parser.add_argument("--data", type=str, required=True, help="Path to datasets directory")
    parser.add_argument(
        "--project", type=str, default="../runs", help="Path to save training outputs"
    )
    parser.add_argument(
        "--model", type=str, default="../weights/yolo26n.pt", help="YOLO model size"
    )
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    return parser.parse_args()


# Creates a yaml file with paths to the splits of each dataset.
def create_combined_yaml(data_dir, datasets, yaml_path):
    train_paths = "\n  - ".join([str(data_dir / dataset / "train/images") for dataset in datasets])
    valid_paths = "\n  - ".join([str(data_dir / dataset / "valid/images") for dataset in datasets])
    test_paths = "\n  - ".join([str(data_dir / dataset / "test/images") for dataset in datasets])

    # Save the text of what the yaml will look like.
    yaml_content = (
        f"train:\n  - {train_paths}\n\nval:\n  - {valid_paths}\n\n"
        f"test:\n  - {test_paths}\n\nnc: 1\nnames: ['drone']\n"
    )

    # Writes the text to the file.
    with open(yaml_path, "w") as f:
        f.write(yaml_content)


# Datasets are weighted based on frequency so that after weighting each dataset has roughly
# the same number of images. This is done by providing multiple references to the smaller
# datasets in the training split until the amount of images matches up.
def create_weighted_yaml(data_dir, datasets, weights, yaml_path):
    # Create multiple paths to the dataset based on its weight
    dataset_paths = []
    for dataset, weight in zip(datasets, weights, strict=True):
        for _ in range(weight):
            dataset_paths.append(f"  - {data_dir / dataset / 'train/images'}")

    valid_paths = "\n  - ".join([str(data_dir / dataset / "valid/images") for dataset in datasets])
    test_paths = "\n  - ".join([str(data_dir / dataset / "test/images") for dataset in datasets])

    # Save the text of what the yaml will look like.
    dataset_paths = "\n".join(dataset_paths)
    yaml_content = f"""train:
    - {dataset_paths}

    val:
    - {valid_paths}

    test:
    - {test_paths}

    nc: 1
    names: ['drone']
    """

    # Writes the text to the file.
    with open(yaml_path, "w") as f:
        f.write(yaml_content)


# Condensed training loop that works for each dataset, assuming the directory structures
# are all the same.
def train(args):
    # Get the data and project directories.
    data_dir = Path(args.data).resolve()
    project_dir = Path(args.project).resolve()

    # Creates the directory to hold all of the new yamls.
    yaml_dir = project_dir / "experiment_yamls"
    yaml_dir.mkdir(parents=True, exist_ok=True)

    # Save specific datasets that should all be trained with YOLOv8.
    experiments = [
        {
            "name": "thermal_all_weighted",
            "datasets": [
                "zenodo_thermal_no_augmentation",
                "anti_uav_thermal_no_augmentation",
                "halmstad_thermal_no_augmentation",
            ],
            "weighted": True,
            "weights": [17, 1, 3],
        }
    ]

    # Simple training loop for each experiment.
    for experiment in experiments:
        print("---------------------------------------")
        print(f"Training {experiment['name']}")
        print("---------------------------------------\n")

        # Define the yaml path for the combined datasets.
        yaml_path = yaml_dir / f"{experiment['name']}.yaml"

        # Add the weights if the experiment is weighted.
        if experiment["weighted"]:
            create_weighted_yaml(data_dir, experiment["datasets"], experiment["weights"], yaml_path)
        else:
            create_combined_yaml(data_dir, experiment["datasets"], yaml_path)

        # Loads the model (options include yolov8n.pt (smallest), yolov8s.pt,
        # yolov8m.pt, yolov8l.pt, yolov8x.pt)
        model = YOLO(args.model)

        # Train the experiment, looking at specific arguments.
        result = model.train(
            exist_ok=True,
            data=str(yaml_path),
            project=str(project_dir),
            name=experiment["name"],
            epochs=args.epochs,
        )

        print("---------------------------------------")
        print(f"\nEvaluating {experiment['name']}")
        print("---------------------------------------\n")

        # Evaluate the best model performance for each experiment on the test set of that
        # experiment.
        model = YOLO(str(Path(result.save_dir) / "weights/best.pt"))
        model.val(
            exist_ok=True,
            split="test",
            plots=True,
            data=str(yaml_path),
            project=str(project_dir),
            name=experiment["name"] + "_val",
        )


if __name__ == "__main__":
    args = parse_args()
    train(args)
