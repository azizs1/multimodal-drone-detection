from pathlib import Path

import cv2
from mcos_decoder import load_groundtruth
from sklearn.model_selection import train_test_split

# Configure paths to the current dataset and where the processed dataset will go, in addition for
# how many frames to sample.
DATASET_PATH = Path("datasets/halmstad_multi_sensor/Data")
THERMAL_OUTPUT = Path("datasets/halmstad_thermal_no_augmentation")
VISUAL_OUTPUT = Path("datasets/halmstad_visual_no_augmentation")
SAMPLE_RATE = 10


# Convert the given JSON pixel coordinates to YOLO.
def convert_to_yolo(box, img_width, img_height):
    x, y, w, h = box
    cx = (x + w / 2) / img_width
    cy = (y + h / 2) / img_height
    w_norm = w / img_width
    h_norm = h / img_height
    return cx, cy, w_norm, h_norm


# Since the halmstad data doesn't come pre-split, this function will apply a split consistent with
# the other datasets (70% train, 15% test, 15% valid).
def assign_splits(video_files):
    # Uses Sci-kit learn to split the videos into the train, test, and valid splits.
    train_videos, temp_videos = train_test_split(list(video_files), test_size=0.3, random_state=23)
    valid_videos, test_videos = train_test_split(temp_videos, test_size=0.5, random_state=23)

    return [(test_videos, "test"), (train_videos, "train"), (valid_videos, "valid")]


# For a single video and .mat file, extract the frames and the labels.
def extract_video(video_path, label_path, output_images, output_labels, is_drone):
    # Must run this function to read the .mat file in python
    # (from original halmstad dataset README.md).
    bboxes = load_groundtruth(str(label_path))

    # Start reading the video and get the sizes of the frames for the labels later.
    cap = cv2.VideoCapture(str(video_path))
    img_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    img_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Loop through every single frame in the video.
    frame_idx = 0
    saved = 0
    while cap.isOpened():
        ret, frame = cap.read()

        # Breaks when the video runs out of frames.
        if not ret:
            break

        if frame_idx >= len(bboxes):
            break

        # Extract the bounding box for each frame.
        box = bboxes[frame_idx]

        # Save if the frame is one of the frames in the sample rate or if the frame is a
        # negative example.
        if frame_idx % SAMPLE_RATE == 0:
            img_name = f"{video_path.stem}_{str(frame_idx).zfill(3)}.jpg"
            label_name = img_name.replace(".jpg", ".txt")

            # Save new image.
            cv2.imwrite(str(output_images / img_name), frame)

            # Write the YOLO converted label file if a drone is present, otherwise, just leave the
            # empty label file there.
            with open(output_labels / label_name, "w") as f:
                if is_drone and box is not None:
                    cx, cy, w_norm, h_norm = convert_to_yolo(box, img_width, img_height)
                    f.write(f"0 {cx:.6f} {cy:.6f} {w_norm:.6f} {h_norm:.6f}\n")

            saved += 1

        frame_idx += 1

    cap.release()
    return saved


# Loop through all videos through each split and each modality.
def preprocess():
    # Create output directories and subdirectories.
    for output_path in [THERMAL_OUTPUT, VISUAL_OUTPUT]:
        for split in ["train", "valid", "test"]:
            (output_path / split / "images").mkdir(parents=True, exist_ok=True)
            (output_path / split / "labels").mkdir(parents=True, exist_ok=True)

    # Extracts the image and label information from all images in all videos, and puts them in
    # their dedicated splits.
    for modality in ["Video_IR", "Video_V"]:
        print(f"\n-- {modality} --------------------------")

        # Gather all of the video files and assign splits for each one.
        video_files = sorted((DATASET_PATH / modality).glob("*.mp4"))
        split_list = assign_splits(video_files)

        # Loop through each split, and then each video.
        total_saved = 0
        for split_videos, split in split_list:
            for video_path in split_videos:
                # Configure paths to the labels and the output based on the modality.
                label_path = (
                    DATASET_PATH / modality / video_path.name.replace(".mp4", "_LABELS.mat")
                )
                output_path = THERMAL_OUTPUT if modality == "Video_IR" else VISUAL_OUTPUT

                # Extract the video.
                saved = extract_video(
                    video_path,
                    label_path,
                    output_path / split / "images",
                    output_path / split / "labels",
                    "DRONE" in video_path.name.upper(),
                )
                total_saved += saved

        print(f"Saved {total_saved} frames")

    # Writes a data.yaml for each modality to mirror the zenodo datasets.
    for output_path in [THERMAL_OUTPUT, VISUAL_OUTPUT]:
        yaml_content = (
            "train: train/images\nval: valid/images\ntest: test/images\nnc: 1\nnames: ['drone']"
        )

        # Writes the text to the file.
        with open(output_path / "data.yaml", "w") as f:
            f.write(yaml_content)

    # Displays output.
    print("\nPreprocessing complete")
    print(f"Thermal output: {THERMAL_OUTPUT}")
    print(f"Visual output: {VISUAL_OUTPUT}")


if __name__ == "__main__":
    preprocess()
