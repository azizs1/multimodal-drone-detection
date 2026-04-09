import shutil
import sys
from pathlib import Path
from ultralytics import YOLO
import os
import cv2
import random

#Store dataset, temp directory, and model paths.
DATASET_PATH = Path("datasets/zenodo_thermal_no_augmentation")
TEMP_DIR = Path("missing_labels")
MODEL_PATH = Path("weights/thermal_no_augmentation_best.pt")

#Extract each image with missing labels from each of the zenodo_thermal_no_augmentation splits.
def extract():
    #Keep a count variable to make sure numbers line up with data exploration.
    count = 0

    #Loop through each split.
    for split in ["train", "test", "valid"]:
        os.makedirs(TEMP_DIR / split / "original_images")
        os.makedirs(TEMP_DIR / split / "missing_labels")

        #Loops through each of the images in the split and moves the ones with blank labels
        for image_name in os.listdir(DATASET_PATH / split / "images"):

            #Make paths to the images and labels.
            image_path = DATASET_PATH / split / "images" / image_name
            label_name = image_name.replace(".jpg", ".txt")
            label_path = DATASET_PATH / split / "labels" / label_name

            #Moves the images and labels if the labels don't have anything in them
            if os.path.getsize(label_path) == 0:
                shutil.move(image_path, TEMP_DIR / split / "original_images" / image_name)
                shutil.move(label_path, TEMP_DIR / split / "missing_labels" / label_name)
                count += 1
    
    print(f"  Moved {count} unlabeled images")

#Predict the labels for the images with missing ones. With high model accuracy, these labels in theory should be accurate as well.
#Save will save the images with the bounding boxes already created in addition to the updated labels.
def predict():
    model = YOLO(str(MODEL_PATH))

    for split in ["train", "test", "valid"]:
        model.predict(
            source=str(TEMP_DIR / split / "original_images"),
            save=True,
            save_txt=True,
            project=str(TEMP_DIR.resolve() / split),
            name="predictions",
        )

#Visualizes the predictions YOLO made to see if they are accurate.
def visualize():
    for split in ["train", "test", "valid"]:
        prediction_images = TEMP_DIR / split / "predictions"
        images_list = list(prediction_images.glob("*.jpg"))

        #Displays each image in another window and moves to the next image after a key is pressed.
        #Press q to exit out of the window.
        for image_path in images_list:
            image = cv2.imread(str(image_path))
            cv2.imshow(f"{split}: {image_path.name}", image)

            #Waits for a key to be pressed. If it is q, exit out of the window
            key = cv2.waitKey(0)
            cv2.destroyAllWindows()
            if key == ord("q"):
                break


#Move all of the images with their new labels back to the original dataset.
def restore():
    #Make sure counts line up with everything.
    img_count = 0
    predictions_count = 0

    #Loop through each split.
    for split in ["train", "test", "valid"]:
        pred_labels_path = TEMP_DIR / split / "predictions" / "labels"

        #Move images back.
        for image_name in os.listdir(TEMP_DIR / split / "original_images"):
            shutil.move(
                TEMP_DIR / split / "original_images" / image_name,
                DATASET_PATH / split / "images" / image_name
            )
            img_count += 1

        #Move predicted labels back.
        for label_name in os.listdir(pred_labels_path):
            shutil.move(
                pred_labels_path / label_name,
                DATASET_PATH / split / "labels" / label_name
            )
            predictions_count += 1

    print(f"Images moved back: {img_count}")
    print(f"Labels updated and moved back: {predictions_count}")

#Define different user inputs to run the specified function.
STEPS = {
    "extract":   extract,
    "predict":   predict,
    "visualize": visualize,
    "restore":   restore,
}

#Reads input for what function to run.
if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in STEPS:
        print("Usage: python src/preprocessing_zenodo.py <function_name>")
        sys.exit(1)

    STEPS[sys.argv[1]]()