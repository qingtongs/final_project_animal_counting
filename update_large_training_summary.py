from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUN = ROOT / "runs" / "animal_openimages3000_yolov8n_e20_gpu"


def main() -> None:
    with (RUN / "results.csv").open("r", encoding="utf-8") as f:
        row = list(csv.DictReader(f))[-1]

    summary = {
        "dataset": "Open Images V7 animal subset exported to YOLO format",
        "train_images": 3000,
        "val_images": 600,
        "train_boxes": 5858,
        "val_boxes": 863,
        "available_classes": 19,
        "missing_class": "wolf (not an independent Open Images class)",
        "model": "YOLOv8n pretrained -> 20-class animal head",
        "epochs": 20,
        "image_size": 512,
        "batch": 16,
        "device": "RTX 3070 Ti Laptop GPU",
        "precision": float(row["metrics/precision(B)"]),
        "recall": float(row["metrics/recall(B)"]),
        "map50": float(row["metrics/mAP50(B)"]),
        "map5095": float(row["metrics/mAP50-95(B)"]),
        "weights": str(RUN / "weights" / "best.pt"),
        "project_val_best_conf": 0.15,
        "project_val_score_after_training": 35.67,
        "project_val_score_yoloworld_zero_shot": 37.58,
        "previous_small_dataset_map50": 0.29652,
        "previous_small_dataset_map5095": 0.23838,
        "previous_small_dataset_project_score": 19.58,
        "note": "Larger Open Images training improves both bbox mAP and synthetic validation dictionary score, but YOLO-World remains slightly better on the provided synthetic validation set.",
    }
    (ROOT / "training_summary_large.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(ROOT / "training_summary_large.json")


if __name__ == "__main__":
    main()
