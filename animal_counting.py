from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional


ANIMAL_CATEGORIES: List[str] = [
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


LABEL_ALIASES: Mapping[str, str] = {
    "kitty": "cat",
    "kitten": "cat",
    "puppy": "dog",
    "pony": "horse",
    "cattle": "cow",
    "calf": "cow",
    "boar": "pig",
    "hog": "pig",
    "bunny": "rabbit",
    "hare": "rabbit",
    "hen": "chicken",
    "rooster": "chicken",
    "chick": "chicken",
    "waterfowl": "duck",
    "gosling": "goose",
    "fawn": "deer",
    "ape": "monkey",
    "vulpes": "fox",
    "ursus": "bear",
}


@dataclass(frozen=True)
class DetectionConfig:
    model: str = "yolov8s-worldv2.pt"
    confidence: float = 0.08
    iou: float = 0.50
    image_size: int = 1280
    max_detections: int = 300


def normalize_label(label: str) -> Optional[str]:
    clean = label.strip().lower().replace("_", " ").replace("-", " ")
    clean = clean.split(",")[0].strip()
    clean = LABEL_ALIASES.get(clean, clean)
    if clean in ANIMAL_CATEGORIES:
        return clean
    return None


class AnimalCounter:
    def __init__(self, config: DetectionConfig | None = None) -> None:
        self.config = config or DetectionConfig()
        self.model = self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO, YOLOWorld
        except Exception as exc:
            raise RuntimeError(
                "Ultralytics is required. Install dependencies with: "
                "python -m pip install -r requirements.txt"
            ) from exc

        model_name = str(self.config.model).lower()
        if "world" in model_name:
            model = YOLOWorld(self.config.model)
            model.set_classes(ANIMAL_CATEGORIES)
        else:
            model = YOLO(self.config.model)
        return model

    def count_image(self, image_path: str | Path) -> Dict[str, int]:
        image_path = Path(image_path)
        results = self.model.predict(
            source=str(image_path),
            conf=self.config.confidence,
            iou=self.config.iou,
            imgsz=self.config.image_size,
            max_det=self.config.max_detections,
            agnostic_nms=True,
            verbose=False,
        )

        counts: Counter[str] = Counter()
        for result in results:
            names = result.names or {}
            boxes = getattr(result, "boxes", None)
            if boxes is None or boxes.cls is None:
                continue
            for cls_id in boxes.cls.tolist():
                raw_label = names.get(int(cls_id), str(cls_id))
                label = normalize_label(raw_label)
                if label:
                    counts[label] += 1

        return dict(sorted(counts.items()))


def iter_image_files(image_dir: str | Path) -> Iterable[Path]:
    image_dir = Path(image_dir)
    suffixes = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    return sorted(p for p in image_dir.iterdir() if p.suffix.lower() in suffixes)
