import cv2
import json
from pathlib import Path

#Configure paths to the current dataset and where the processed dataset will go, in addition for how many frames to sample.
DATASET_PATH = Path("datasets/anti_uav")
THERMAL_OUTPUT = Path("datasets/anti_uav_thermal_no_augmentation")
VISUAL_OUTPUT = Path("datasets/anti_uav_visual_no_augmentation")
SAMPLE_RATE = 10

#Convert the given JSON pixel coordinates to YOLO.
def convert_to_yolo(box, img_width, img_height):
    x, y, w, h = box
    cx = (x + w / 2) / img_width
    cy = (y + h / 2) / img_height
    w_norm = w / img_width
    h_norm = h / img_height
    return cx, cy, w_norm, h_norm

#For a single video and JSON file, extract the frames and the labels.
def extract_sequence(sequence_path, output_images, output_labels, modality):
    #File paths (infared instead of thermal and visible instead of visual).
    mapped_modality = "infrared" if modality == "thermal" else "visible"
    video_path = sequence_path / f"{mapped_modality}.mp4"
    json_path = sequence_path / f"{mapped_modality}.json"
    
    #Read the JSON.
    with open(json_path) as f:
        data = json.load(f)

    #Start reading the video and get the sizes of the frames for the labels later.
    cap = cv2.VideoCapture(str(video_path))
    img_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    img_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    #Loop through every single frame in the video.
    frame_idx = 0
    saved = 0
    while cap.isOpened():
        ret, frame = cap.read()

        #Breaks when the video runs out of frames.
        if not ret:
            break

        #Extract the label and bounding box for each frame.
        exist = data['exist'][frame_idx]
        box = data['gt_rect'][frame_idx]

        #Save if the frame is one of the frames in the sample rate or if the frame is a negative example.
        if frame_idx % SAMPLE_RATE == 0:
            img_name = f"{sequence_path.name}_{modality}_{str(frame_idx).zfill(3)}.jpg"
            label_name = img_name.replace(".jpg", ".txt")

            #Save new image.
            cv2.imwrite(str(output_images / img_name), frame)

            #Write the YOLO converted label file if a drone is present, otherwise, just leave the empty label file there.
            with open(output_labels / label_name, 'w') as f:
                if exist == 1:
                    cx, cy, w_norm, h_norm = convert_to_yolo(box, img_width, img_height)
                    f.write(f"0 {cx:.6f} {cy:.6f} {w_norm:.6f} {h_norm:.6f}\n")

            saved += 1

        frame_idx += 1

    cap.release()
    return saved

#Loop through all videos through each split and each modality.
def preprocess():
    #Create output directories and subdirectories.
    for output_path in [THERMAL_OUTPUT, VISUAL_OUTPUT]:
        for split in ["train", "valid", "test"]:
            (output_path / split / "images").mkdir(parents=True, exist_ok=True)
            (output_path / split / "labels").mkdir(parents=True, exist_ok=True)

    #Extracts the image and label information for each image in path in each modality in each split.
    for split in ["train", "val", "test"]:
        output_split = "valid" if split == "val" else split
        print(f"\n-- {split} --------------------------")
        sequences = [dir for dir in (DATASET_PATH / split).iterdir() if dir.is_dir()]
        total_saved = 0

        for sequence in sequences:
            for modality, output_path in [("thermal", THERMAL_OUTPUT), ("visual", VISUAL_OUTPUT)]:
                saved = extract_sequence(
                    sequence,
                    output_path / output_split / "images",
                    output_path / output_split / "labels",
                    modality
                )
                total_saved += saved

        print(f"Saved {total_saved} frames")

    #Writes a data.yaml for each modality to mirror the zenodo datasets.
    for output_path in [THERMAL_OUTPUT, VISUAL_OUTPUT]:
        yaml_content = f"train: train/images\nval: valid/images\ntest: test/images\nnc: 1\nnames: ['drone']"

        #writes the text to the file.
        with open(output_path / "data.yaml", 'w') as f:
            f.write(yaml_content)
    
    #Displays output.
    print("\nPreprocessing complete")
    print(f"Thermal output: {THERMAL_OUTPUT}")
    print(f"Visual output: {VISUAL_OUTPUT}")

if __name__ == "__main__":
    preprocess()