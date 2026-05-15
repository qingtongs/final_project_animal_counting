# Animal Detection and Counting Final Project

This project implements the required pipeline for the Deep Learning final project:
single-image animal recognition/counting and batch JSON prediction export.

## Supported Categories

`cat, dog, horse, cow, sheep, goat, pig, rabbit, chicken, duck, goose, deer, monkey, fox, wolf, bear, tiger, lion, zebra, giraffe`

## Install

```powershell
python -m pip install -r requirements.txt
```

The default detector is YOLO-World through `ultralytics`, using
`yolov8s-worldv2.pt`. The model weight is downloaded automatically on first run.

## Run on Evaluation Images

```powershell
python evaluate.py --image-dir path\to\eval_set --output predictions.json
```

Useful tuning options:

```powershell
python evaluate.py --image-dir path\to\eval_set --output predictions.json --conf 0.08 --iou 0.50 --imgsz 1280
```

## Train on Open Images Subset

The project builds a real YOLO-format training subset from Open Images V7. The
current submitted training run uses the larger subset below:

```powershell
$env:PYTHONPATH="E:\Final_Project_Animal_Counting\python_deps"
$env:FIFTYONE_DATABASE_DIR="E:\animal_datasets\fiftyone_db"
python prepare_openimages_dataset.py --root E:/animal_datasets/openimages_animals_3000 --train-samples 3000 --val-samples 600
```

Train with the E-drive virtual environment:

```powershell
E:\Final_Project_Animal_Counting\.venv\Scripts\python.exe train_yolo.py --data E:/animal_datasets/openimages_animals_3000/animal_openimages.yaml --model yolov8n.pt --epochs 20 --imgsz 512 --batch 16 --device 0 --name animal_openimages3000_yolov8n_e20_gpu
```

## Larger Training Run

A larger Open Images V7 animal subset was also prepared:

- 3000 training images
- 600 validation images
- 5858 training boxes
- 863 validation boxes
- 19 available project classes; `wolf` is not available as an independent Open Images class

Training command:

```powershell
E:\Final_Project_Animal_Counting\.venv\Scripts\python.exe train_yolo.py --data E:/animal_datasets/openimages_animals_3000/animal_openimages.yaml --model yolov8n.pt --epochs 20 --imgsz 512 --batch 16 --device 0 --name animal_openimages3000_yolov8n_e20_gpu
```

Large-run results:

- Precision: 0.633
- Recall: 0.423
- mAP50: 0.504
- mAP50-95: 0.405
- Synthetic validation dictionary score: 35.67 at confidence 0.15

Best weights:

```text
runs/animal_openimages3000_yolov8n_e20_gpu/weights/best.pt
```

## Fine-tune with Extra Data

The `extradata` folder is prepared for later fine-tuning:

```text
extradata/
  animal_extradata.yaml
  classes.txt
  images/train/
  images/val/
  labels/train/
  labels/val/
```

Put new labeled images into `extradata/images/train` and
`extradata/images/val`. Put matching YOLO label files into
`extradata/labels/train` and `extradata/labels/val`.

Each image needs a matching `.txt` label file with the same base name:

```text
images/train/dog_001.jpg
labels/train/dog_001.txt
```

Label format:

```text
class_id x_center y_center width height
```

Class IDs must follow `extradata/classes.txt`.

Fine-tune from the current large-run model:

```powershell
E:\Final_Project_Animal_Counting\.venv\Scripts\python.exe finetune_extra.py --epochs 10 --imgsz 512 --batch 16 --device 0
```

The fine-tuned model will be saved to:

```text
runs/animal_extradata_finetune/weights/best.pt
```

Evaluate with the fine-tuned model by editing `animal_counting.py` to use the
new weight path, or by loading this weight in the inference script you use for
submission.

## Validation Format Check

The provided validation set includes `ground_truth.json`, so this command creates a
known-correct validation JSON for checking the required output format:

```powershell
python evaluate.py --image-dir val_set --truth-json val_set\ground_truth.json --output val_predictions.json
python score_predictions.py --truth val_set\ground_truth.json --pred val_predictions.json
```

Do not use `--truth-json` for the final hidden evaluation set. It is only a local
validation shortcut because the validation labels are included in the released files.
