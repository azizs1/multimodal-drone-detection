import shutil
from pathlib import Path
import os

#Store dataset, temp directory, and model paths.
DATASET_PATH = Path("datasets/zenodo_thermal_no_augmentation")
TEMP_DIR = Path("missing_labels")

#Extract each image with missing labels from each of the zenodo_thermal_no_augmentation splits.
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
    
#Remove the temp directory to get rid of the unlabeled labels.
shutil.rmtree(TEMP_DIR)
print(f"  Removed {count} unlabeled images and labels")