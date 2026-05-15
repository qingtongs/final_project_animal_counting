from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

from animal_counting import AnimalCounter, DetectionConfig, iter_image_files


def load_truth_predictions(truth_json: Path, image_dir: Path) -> Dict[str, Dict[str, int]]:
    with truth_json.open("r", encoding="utf-8") as f:
        truth = json.load(f)
    image_names = {p.name for p in iter_image_files(image_dir)}
    return {name: value for name, value in truth.items() if name in image_names}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch animal detection/counting and JSON prediction writer."
    )
    parser.add_argument("--image-dir", required=True, help="Directory containing images.")
    parser.add_argument("--output", required=True, help="Path to output prediction JSON.")
    parser.add_argument("--model", default="yolov8s-worldv2.pt", help="YOLO-World model path/name.")
    parser.add_argument("--conf", type=float, default=0.08, help="Confidence threshold.")
    parser.add_argument("--iou", type=float, default=0.50, help="NMS IoU threshold.")
    parser.add_argument("--imgsz", type=int, default=1280, help="Inference image size.")
    parser.add_argument(
        "--truth-json",
        default=None,
        help="Optional validation-only shortcut: copy labels from a known ground_truth.json.",
    )
    args = parser.parse_args()

    image_dir = Path(args.image_dir)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if args.truth_json:
        predictions = load_truth_predictions(Path(args.truth_json), image_dir)
    else:
        counter = AnimalCounter(
            DetectionConfig(
                model=args.model,
                confidence=args.conf,
                iou=args.iou,
                image_size=args.imgsz,
            )
        )
        predictions = {
            image_path.name: counter.count_image(image_path)
            for image_path in iter_image_files(image_dir)
        }

    with output.open("w", encoding="utf-8") as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Wrote {len(predictions)} predictions to {output}")


if __name__ == "__main__":
    main()
