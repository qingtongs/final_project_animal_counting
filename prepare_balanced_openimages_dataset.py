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
    "Bear": "bear",
    "Tiger": "tiger",
    "Lion": "lion",
    "Zebra": "zebra",
    "Giraffe": "giraffe",
}


def write_data_yaml(dataset_root: Path) -> None:
    names = "\n".join(f"  {i}: {name}" for i, name in enumerate(PROJECT_CLASSES))
    yaml = f"""path: {dataset_root.as_posix()}
train: images/train
val: images/val
test:
names:
{names}
"""
    (dataset_root / "animal_openimages_balanced.yaml").write_text(yaml, encoding="utf-8")


def patch_yolo_labels(label_dir: Path) -> None:
    old_to_new = {old_idx: PROJECT_CLASSES.index(new_name) for old_idx, new_name in enumerate(OPEN_IMAGES_MAP.values())}
    for txt in label_dir.glob("*.txt"):
        rows = []
        for line in txt.read_text(encoding="utf-8").splitlines():
            parts = line.strip().split()
            if len(parts) != 5:
                continue
            old_idx = int(float(parts[0]))
            if old_idx in old_to_new:
                rows.append(" ".join([str(old_to_new[old_idx]), *parts[1:]]))
        txt.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")


def load_balanced_split(split: str, per_class: int, zoo_dir: Path):
    import fiftyone as fo
    import fiftyone.zoo as foz

    merged_name = f"animal-balanced-{split}-{per_class}"
    if fo.dataset_exists(merged_name):
        fo.delete_dataset(merged_name)
    merged = fo.Dataset(merged_name)
    merged.persistent = False

    for oi_label in OPEN_IMAGES_MAP:
        part_name = f"{merged_name}-{oi_label.replace(' ', '_')}"
        if fo.dataset_exists(part_name):
            fo.delete_dataset(part_name)
        print(f"Loading {split} class={oi_label} max={per_class}", flush=True)
        part = foz.load_zoo_dataset(
            "open-images-v7",
            split=split,
            label_types=["detections"],
            classes=[oi_label],
            only_matching=True,
            max_samples=per_class,
            dataset_name=part_name,
            overwrite=False,
        )
        merged.merge_samples(part)
        fo.delete_dataset(part_name)

    return merged


def export_split(dataset, split: str, dataset_root: Path, overwrite: bool) -> None:
    import fiftyone as fo

    yolo_split = "val" if split == "validation" else split
    dataset.export(
        export_dir=str(dataset_root),
        dataset_type=fo.types.YOLOv5Dataset,
        label_field="ground_truth",
        split=yolo_split,
        classes=list(OPEN_IMAGES_MAP),
        overwrite=overwrite,
    )
    patch_yolo_labels(dataset_root / "labels" / yolo_split)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="E:/animal_datasets/openimages_animals_balanced")
    parser.add_argument("--zoo-dir", default="E:/animal_datasets/fiftyone_zoo")
    parser.add_argument("--train-per-class", type=int, default=250)
    parser.add_argument("--val-per-class", type=int, default=60)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    dataset_root = Path(args.root)
    zoo_dir = Path(args.zoo_dir)
    os.environ.setdefault("FIFTYONE_DATABASE_DIR", "E:/animal_datasets/fiftyone_db")
    zoo_dir.mkdir(parents=True, exist_ok=True)
    if args.reset and dataset_root.exists():
        shutil.rmtree(dataset_root)
    dataset_root.mkdir(parents=True, exist_ok=True)

    import fiftyone as fo

    fo.config.dataset_zoo_dir = str(zoo_dir)
    train = load_balanced_split("train", args.train_per_class, zoo_dir)
    export_split(train, "train", dataset_root, overwrite=True)
    val = load_balanced_split("validation", args.val_per_class, zoo_dir)
    export_split(val, "validation", dataset_root, overwrite=False)
    write_data_yaml(dataset_root)
    print(dataset_root / "animal_openimages_balanced.yaml")


if __name__ == "__main__":
    main()
