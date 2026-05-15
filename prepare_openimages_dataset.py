from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


PROJECT_CLASSES = [
    "cat",
    "dog",
    "horse",
    "cow",
    "sheep",
    "goat",
    "pig",
    "rabbit",
    "chicken",
    "duck",
    "goose",
    "deer",
    "monkey",
    "fox",
    "wolf",
    "bear",
    "tiger",
    "lion",
    "zebra",
    "giraffe",
]


OPEN_IMAGES_MAP = {
    "Cat": "cat",
    "Dog": "dog",
    "Horse": "horse",
    "Cattle": "cow",
    "Sheep": "sheep",
    "Goat": "goat",
    "Pig": "pig",
    "Rabbit": "rabbit",
    "Chicken": "chicken",
    "Duck": "duck",
    "Goose": "goose",
    "Deer": "deer",
    "Monkey": "monkey",
    "Fox": "fox",
    # Open Images V7 does not expose a specific Wolf detector class in the
    # Ultralytics class list. Keep wolf in data.yaml so the prediction format
    # still matches the project, but it will have no downloaded training images.
    "Bear": "bear",
    "Tiger": "tiger",
    "Lion": "lion",
    "Zebra": "zebra",
    "Giraffe": "giraffe",
}


def patch_yolo_labels(label_dir: Path) -> None:
    old_to_new = {old_idx: PROJECT_CLASSES.index(new_name) for old_idx, new_name in enumerate(OPEN_IMAGES_MAP.values())}
    for txt in label_dir.glob("*.txt"):
        rows = []
        for line in txt.read_text(encoding="utf-8").splitlines():
            parts = line.strip().split()
            if len(parts) != 5:
                continue
            old_idx = int(float(parts[0]))
            if old_idx not in old_to_new:
                continue
            rows.append(" ".join([str(old_to_new[old_idx]), *parts[1:]]))
        txt.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")


def write_data_yaml(dataset_root: Path) -> None:
    names = "\n".join(f"  {i}: {name}" for i, name in enumerate(PROJECT_CLASSES))
    yaml = f"""path: {dataset_root.as_posix()}
train: images/train
val: images/val
test:
names:
{names}
"""
    (dataset_root / "animal_openimages.yaml").write_text(yaml, encoding="utf-8")


def export_split(split: str, max_samples: int, dataset_root: Path, zoo_dir: Path) -> None:
    import fiftyone as fo
    import fiftyone.zoo as foz

    fo.config.dataset_zoo_dir = str(zoo_dir)
    oi_classes = list(OPEN_IMAGES_MAP)
    yolo_split = "val" if split == "validation" else split
    name = f"animal-openimages-{split}-{max_samples}"

    dataset = foz.load_zoo_dataset(
        "open-images-v7",
        split=split,
        label_types=["detections"],
        classes=oi_classes,
        only_matching=True,
        max_samples=max_samples,
        dataset_name=name,
        overwrite=False,
    )
    dataset.export(
        export_dir=str(dataset_root),
        dataset_type=fo.types.YOLOv5Dataset,
        label_field="ground_truth",
        split=yolo_split,
        classes=oi_classes,
        overwrite=(split == "train"),
    )

    patch_yolo_labels(dataset_root / "labels" / yolo_split)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="E:/animal_datasets/openimages_animals")
    parser.add_argument("--zoo-dir", default="E:/animal_datasets/fiftyone_zoo")
    parser.add_argument("--train-samples", type=int, default=1200)
    parser.add_argument("--val-samples", type=int, default=300)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    dataset_root = Path(args.root)
    zoo_dir = Path(args.zoo_dir)
    if args.reset and dataset_root.exists():
        shutil.rmtree(dataset_root)
    dataset_root.mkdir(parents=True, exist_ok=True)
    zoo_dir.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("FIFTYONE_DATABASE_DIR", str(Path("E:/animal_datasets/fiftyone_db")))

    export_split("train", args.train_samples, dataset_root, zoo_dir)
    export_split("validation", args.val_samples, dataset_root, zoo_dir)
    write_data_yaml(dataset_root)
    print(dataset_root / "animal_openimages.yaml")


if __name__ == "__main__":
    main()
