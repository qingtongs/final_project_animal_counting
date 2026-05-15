from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = PROJECT_ROOT / "extradata" / "animal_extradata.yaml"
DEFAULT_BASE_MODEL = (
    PROJECT_ROOT
    / "runs"
    / "animal_openimages3000_yolov8n_e20_gpu"
    / "weights"
    / "best.pt"
)
DEFAULT_RUNS = PROJECT_ROOT / "runs"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def count_images(path: Path) -> int:
    return sum(1 for item in path.iterdir() if item.suffix.lower() in IMAGE_EXTENSIONS)


def validate_extra_dataset(data_yaml: Path) -> None:
    extra_root = data_yaml.parent
    required_dirs = [
        extra_root / "images" / "train",
        extra_root / "images" / "val",
        extra_root / "labels" / "train",
        extra_root / "labels" / "val",
    ]
    missing = [str(path) for path in required_dirs if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required extra dataset folders:\n" + "\n".join(missing))

    train_images = count_images(extra_root / "images" / "train")
    val_images = count_images(extra_root / "images" / "val")
    if train_images == 0 or val_images == 0:
        raise RuntimeError(
            "Extra dataset is empty. Add images and matching YOLO label files to "
            "extradata/images/train, extradata/labels/train, extradata/images/val, "
            "and extradata/labels/val before fine-tuning."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune the latest animal model with extradata.")
    parser.add_argument("--data", default=str(DEFAULT_DATA))
    parser.add_argument("--model", default=str(DEFAULT_BASE_MODEL))
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--imgsz", type=int, default=512)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--project", default=str(DEFAULT_RUNS))
    parser.add_argument("--name", default="animal_extradata_finetune")
    parser.add_argument("--device", default="0")
    parser.add_argument("--patience", type=int, default=5)
    args = parser.parse_args()

    data_yaml = Path(args.data).resolve()
    model_path = Path(args.model).resolve()
    if not data_yaml.exists():
        raise FileNotFoundError(f"Extra data yaml not found: {data_yaml}")
    if not model_path.exists():
        raise FileNotFoundError(f"Base model not found: {model_path}")

    validate_extra_dataset(data_yaml)

    model = YOLO(str(model_path))
    results = model.train(
        data=str(data_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=args.project,
        name=args.name,
        device=args.device,
        workers=0,
        patience=args.patience,
        exist_ok=True,
    )
    print(results)
    best = Path(args.project) / args.name / "weights" / "best.pt"
    print(f"best={best}")


if __name__ == "__main__":
    main()
