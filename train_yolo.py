from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="E:/animal_datasets/openimages_animals/animal_openimages.yaml")
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--project", default="E:/Final_Project_Animal_Counting/runs")
    parser.add_argument("--name", default="animal_openimages_yolov8n")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    model = YOLO(args.model)
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=args.project,
        name=args.name,
        device=args.device,
        workers=0,
        patience=5,
        exist_ok=True,
    )
    print(results)
    best = Path(args.project) / args.name / "weights" / "best.pt"
    print(f"best={best}")


if __name__ == "__main__":
    main()
