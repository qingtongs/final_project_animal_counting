from __future__ import annotations

import argparse
import json
import shutil
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


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

WOLF_ID = PROJECT_CLASSES.index("wolf")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def image_for_label(label_path: Path, image_dir: Path) -> Path | None:
    for suffix in IMAGE_SUFFIXES:
        candidate = image_dir / f"{label_path.stem}{suffix}"
        if candidate.exists():
            return candidate
    return None


def read_label_classes(label_path: Path) -> set[int]:
    classes = set()
    for line in label_path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 5:
            classes.add(int(float(parts[0])))
    return classes


def copy_sample(image_path: Path, label_path: Path, out_root: Path, split: str) -> None:
    out_img = out_root / "images" / split / image_path.name
    out_label = out_root / "labels" / split / f"{image_path.stem}.txt"
    out_img.parent.mkdir(parents=True, exist_ok=True)
    out_label.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(image_path, out_img)
    shutil.copy2(label_path, out_label)


def select_balanced_samples(source_root: Path, out_root: Path, split: str, target_per_class: int) -> Counter:
    image_dir = source_root / "images" / split
    label_dir = source_root / "labels" / split
    labels_by_class: dict[int, list[Path]] = defaultdict(list)
    classes_by_label: dict[Path, set[int]] = {}

    for label_path in sorted(label_dir.glob("*.txt")):
        image_path = image_for_label(label_path, image_dir)
        if not image_path:
            continue
        classes = read_label_classes(label_path)
        classes.discard(WOLF_ID)
        if not classes:
            continue
        classes_by_label[label_path] = classes
        for cls_id in classes:
            labels_by_class[cls_id].append(label_path)

    selected: set[Path] = set()
    counts: Counter = Counter()
    class_order = sorted(
        (i for i in range(len(PROJECT_CLASSES)) if i != WOLF_ID),
        key=lambda idx: len(labels_by_class[idx]),
    )

    for cls_id in class_order:
        for label_path in labels_by_class[cls_id]:
            if counts[cls_id] >= target_per_class:
                break
            selected.add(label_path)
            for contained_cls in classes_by_label[label_path]:
                counts[contained_cls] += 1

    copied_counts: Counter = Counter()
    for label_path in sorted(selected):
        image_path = image_for_label(label_path, image_dir)
        if not image_path:
            continue
        copy_sample(image_path, label_path, out_root, split)
        for cls_id in read_label_classes(label_path):
            copied_counts[cls_id] += 1
    return copied_counts


def commons_api(params: dict[str, str]) -> dict:
    query = urllib.parse.urlencode({"format": "json", **params})
    url = f"https://commons.wikimedia.org/w/api.php?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "animal-counting-dataset-builder/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def iter_commons_images(category: str, limit: int) -> Iterable[dict]:
    gcmcontinue = None
    yielded = 0
    while yielded < limit:
        params = {
            "action": "query",
            "generator": "categorymembers",
            "gcmtitle": category,
            "gcmtype": "file",
            "gcmlimit": "50",
            "prop": "imageinfo",
            "iiprop": "url|mime|size",
            "iiurlwidth": "1600",
        }
        if gcmcontinue:
            params["gcmcontinue"] = gcmcontinue
        data = commons_api(params)
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            info = (page.get("imageinfo") or [{}])[0]
            mime = info.get("mime", "")
            if not mime.startswith("image/"):
                continue
            if info.get("width", 0) < 640 or info.get("height", 0) < 480:
                continue
            yielded += 1
            yield {
                "title": page.get("title", ""),
                "url": info.get("thumburl") or info["url"],
                "width": info.get("width"),
                "height": info.get("height"),
            }
            if yielded >= limit:
                break
        gcmcontinue = data.get("continue", {}).get("gcmcontinue")
        if not gcmcontinue:
            break


def download_wolf_candidates(raw_dir: Path, candidate_limit: int) -> list[Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = sorted(
        p for p in raw_dir.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES and p.stat().st_size > 0
    )
    if len(downloaded) >= candidate_limit:
        return downloaded[:candidate_limit]
    for idx, item in enumerate(iter_commons_images("Category:Canis lupus", candidate_limit), start=1):
        suffix = Path(urllib.parse.urlparse(item["url"]).path).suffix.lower()
        if suffix not in IMAGE_SUFFIXES:
            suffix = ".jpg"
        out_path = raw_dir / f"wolf_commons_{idx:04d}{suffix}"
        if out_path.exists():
            downloaded.append(out_path)
            continue
        try:
            request = urllib.request.Request(item["url"], headers={"User-Agent": "animal-counting-dataset-builder/1.0"})
            with urllib.request.urlopen(request, timeout=60) as response:
                out_path.write_bytes(response.read())
            downloaded.append(out_path)
            time.sleep(0.2)
        except Exception as exc:
            safe_title = item["title"].encode("ascii", errors="ignore").decode("ascii")
            print(f"skip download {safe_title}: {exc}")
    return downloaded


def add_full_image_wolves(raw_images: list[Path], out_root: Path, train_count: int, val_count: int) -> tuple[Counter, Counter]:
    train = Counter()
    val = Counter()
    needed = train_count + val_count
    for image_path in raw_images[:needed]:
        split = "train" if train[WOLF_ID] < train_count else "val"
        out_image = out_root / "images" / split / f"wolf_{train[WOLF_ID] + val[WOLF_ID] + 1:04d}{image_path.suffix.lower()}"
        out_label = out_root / "labels" / split / f"{out_image.stem}.txt"
        out_image.parent.mkdir(parents=True, exist_ok=True)
        out_label.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(image_path, out_image)
        out_label.write_text(f"{WOLF_ID} 0.500000 0.500000 1.000000 1.000000\n", encoding="utf-8")
        if split == "train":
            train[WOLF_ID] += 1
        else:
            val[WOLF_ID] += 1
    return train, val


def yolo_box_from_xyxy(xyxy: list[float], width: int, height: int) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = xyxy
    x1 = max(0.0, min(float(width), x1))
    x2 = max(0.0, min(float(width), x2))
    y1 = max(0.0, min(float(height), y1))
    y2 = max(0.0, min(float(height), y2))
    bw = max(0.0, x2 - x1)
    bh = max(0.0, y2 - y1)
    return ((x1 + x2) / 2 / width, (y1 + y2) / 2 / height, bw / width, bh / height)


def add_auto_labeled_wolves(
    raw_images: list[Path],
    out_root: Path,
    train_count: int,
    val_count: int,
    conf: float,
    model_path: str,
) -> Counter:
    from PIL import Image
    from ultralytics import YOLOWorld

    model = YOLOWorld(model_path)
    model.set_classes(["wolf"])

    counts: Counter = Counter()
    accepted = 0
    needed = train_count + val_count
    for image_path in raw_images:
        if accepted >= needed:
            break
        try:
            with Image.open(image_path) as img:
                width, height = img.size
        except Exception:
            continue
        results = model.predict(str(image_path), conf=conf, iou=0.50, imgsz=960, max_det=5, verbose=False)
        rows = []
        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            for xyxy, score in zip(boxes.xyxy.tolist(), boxes.conf.tolist()):
                x, y, w, h = yolo_box_from_xyxy(xyxy, width, height)
                area = w * h
                if score >= conf and 0.01 <= area <= 0.95:
                    rows.append(f"{WOLF_ID} {x:.6f} {y:.6f} {w:.6f} {h:.6f}")
        if not rows:
            continue

        split = "train" if counts["train"] < train_count else "val"
        out_image = out_root / "images" / split / f"wolf_{counts[split] + 1:04d}{image_path.suffix.lower()}"
        out_label = out_root / "labels" / split / f"{out_image.stem}.txt"
        out_image.parent.mkdir(parents=True, exist_ok=True)
        out_label.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(image_path, out_image)
        out_label.write_text("\n".join(rows) + "\n", encoding="utf-8")
        counts[split] += 1
        accepted += 1
    return Counter({WOLF_ID: counts["train"]}), Counter({WOLF_ID: counts["val"]})


def write_data_yaml(out_root: Path) -> None:
    names = "\n".join(f"  {i}: {name}" for i, name in enumerate(PROJECT_CLASSES))
    yaml = f"""path: {out_root.as_posix()}
train: images/train
val: images/val
test:
names:
{names}
"""
    (out_root / "animal_20class_high_quality.yaml").write_text(yaml, encoding="utf-8")


def count_split(out_root: Path, split: str) -> dict[str, int]:
    counts: Counter = Counter()
    for label_path in (out_root / "labels" / split).glob("*.txt"):
        for line in label_path.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) == 5:
                counts[int(float(parts[0]))] += 1
    return {name: counts[i] for i, name in enumerate(PROJECT_CLASSES)}


def write_report(out_root: Path) -> None:
    report = {
        "dataset": str(out_root),
        "yaml": str(out_root / "animal_20class_high_quality.yaml"),
        "classes": PROJECT_CLASSES,
        "train_boxes": count_split(out_root, "train"),
        "val_boxes": count_split(out_root, "val"),
    }
    missing = {
        split: [name for name, count in report[f"{split}_boxes"].items() if count == 0]
        for split in ["train", "val"]
    }
    report["missing_classes"] = missing
    (out_root / "coverage_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if missing["train"] or missing["val"]:
        raise RuntimeError(f"Dataset is missing classes: {missing}")


def reset_output(out_root: Path) -> None:
    if out_root.exists():
        shutil.rmtree(out_root)
    for split in ["train", "val"]:
        (out_root / "images" / split).mkdir(parents=True, exist_ok=True)
        (out_root / "labels" / split).mkdir(parents=True, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a YOLO dataset covering all 20 project animal classes.")
    parser.add_argument("--source-root", default="E:/animal_datasets/openimages_animals_3000")
    parser.add_argument("--output-root", default="E:/animal_datasets/animal_20class_high_quality")
    parser.add_argument("--train-per-class", type=int, default=160)
    parser.add_argument("--val-per-class", type=int, default=40)
    parser.add_argument("--wolf-train", type=int, default=80)
    parser.add_argument("--wolf-val", type=int, default=20)
    parser.add_argument("--wolf-candidates", type=int, default=220)
    parser.add_argument("--wolf-conf", type=float, default=0.18)
    parser.add_argument("--wolf-model", default="yolov8s-worldv2.pt")
    parser.add_argument("--wolf-source-dir", default="E:/animal_datasets/wolf_commons_raw")
    parser.add_argument("--wolf-label-mode", choices=["full-image", "auto"], default="full-image")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    source_root = Path(args.source_root)
    out_root = Path(args.output_root)
    if args.reset:
        reset_output(out_root)
    else:
        out_root.mkdir(parents=True, exist_ok=True)

    train_counts = select_balanced_samples(source_root, out_root, "train", args.train_per_class)
    val_counts = select_balanced_samples(source_root, out_root, "val", args.val_per_class)

    raw_wolf_dir = Path(args.wolf_source_dir)
    wolf_images = download_wolf_candidates(raw_wolf_dir, args.wolf_candidates)
    if args.wolf_label_mode == "auto":
        wolf_train_counts, wolf_val_counts = add_auto_labeled_wolves(
            wolf_images,
            out_root,
            args.wolf_train,
            args.wolf_val,
            args.wolf_conf,
            args.wolf_model,
        )
    else:
        wolf_train_counts, wolf_val_counts = add_full_image_wolves(
            wolf_images,
            out_root,
            args.wolf_train,
            args.wolf_val,
        )
    train_counts.update(wolf_train_counts)
    val_counts.update(wolf_val_counts)

    write_data_yaml(out_root)
    write_report(out_root)


if __name__ == "__main__":
    main()
