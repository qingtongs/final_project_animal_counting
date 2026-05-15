# Animal Detection and Counting Final Project

## Project Overview

This project implements the required pipeline for the Deep Learning final
project: single-image animal recognition/counting and batch JSON prediction
export.

本项目实现深度学习期末项目要求的完整流程：单张图片动物识别与计数，以及批量图片预测结果 JSON 导出。

## Supported Categories / 支持类别

`cat, dog, horse, cow, sheep, goat, pig, rabbit, chicken, duck, goose, deer, monkey, fox, wolf, bear, tiger, lion, zebra, giraffe`

These are the 20 animal classes used by the project.

以上是本项目使用的 20 个动物类别，训练、微调和预测时类别顺序需要保持一致。

## Install / 环境安装

```powershell
python -m pip install -r requirements.txt
```

The default detector is YOLO-World through `ultralytics`, using
`yolov8s-worldv2.pt`. The model weight is downloaded automatically on first run.

默认检测器使用 `ultralytics` 中的 YOLO-World，模型权重为 `yolov8s-worldv2.pt`。第一次运行时会自动下载权重文件。

## Run on Evaluation Images / 在测试图片上运行

```powershell
python evaluate.py --image-dir path\to\eval_set --output predictions.json
```

Useful tuning options:

常用可调参数如下：

```powershell
python evaluate.py --image-dir path\to\eval_set --output predictions.json --conf 0.08 --iou 0.50 --imgsz 1280
```

`--image-dir` is the folder containing evaluation images. `--output` is the JSON
file to save predictions.

`--image-dir` 表示待预测图片文件夹，`--output` 表示保存预测结果的 JSON 文件。

## Train on Open Images Subset / 使用 Open Images 子集训练

The project builds a real YOLO-format training subset from Open Images V7. The
current submitted training run uses the larger subset below:

本项目从 Open Images V7 构建真实的 YOLO 格式动物检测数据集。当前提交版本使用的是下面的大数据集训练配置：

```powershell
$env:PYTHONPATH="E:\Final_Project_Animal_Counting\python_deps"
$env:FIFTYONE_DATABASE_DIR="E:\animal_datasets\fiftyone_db"
python prepare_openimages_dataset.py --root E:/animal_datasets/openimages_animals_3000 --train-samples 3000 --val-samples 600
```

Train with the E-drive virtual environment:

使用 E 盘项目虚拟环境进行训练：

```powershell
E:\Final_Project_Animal_Counting\.venv\Scripts\python.exe train_yolo.py --data E:/animal_datasets/openimages_animals_3000/animal_openimages.yaml --model yolov8n.pt --epochs 20 --imgsz 512 --batch 16 --device 0 --name animal_openimages3000_yolov8n_e20_gpu
```

## Larger Training Run / 大数据集训练结果

A larger Open Images V7 animal subset was prepared:

已准备并训练一个更大的 Open Images V7 动物数据子集：

- 3000 training images / 3000 张训练图片
- 600 validation images / 600 张验证图片
- 5858 training boxes / 5858 个训练标注框
- 863 validation boxes / 863 个验证标注框
- 19 available project classes; `wolf` is not available as an independent Open Images class
- 覆盖 19 个项目类别；`wolf` 在 Open Images 中没有独立类别

Training command:

训练命令：

```powershell
E:\Final_Project_Animal_Counting\.venv\Scripts\python.exe train_yolo.py --data E:/animal_datasets/openimages_animals_3000/animal_openimages.yaml --model yolov8n.pt --epochs 20 --imgsz 512 --batch 16 --device 0 --name animal_openimages3000_yolov8n_e20_gpu
```

Large-run results:

大数据集训练真实结果：

- Precision: 0.633
- Recall: 0.423
- mAP50: 0.504
- mAP50-95: 0.405
- Synthetic validation dictionary score: 35.67 at confidence 0.15
- 合成验证集字典得分：35.67，使用置信度阈值 0.15

Best weights:

最佳模型权重：

```text
runs/animal_openimages3000_yolov8n_e20_gpu/weights/best.pt
```

## Fine-tune with Extra Data / 使用 Extra Data 微调

The `extradata` folder is prepared for later fine-tuning:

项目已经准备好 `extradata` 文件夹，方便后续加入额外数据继续微调：

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

将新标注图片放入 `extradata/images/train` 和 `extradata/images/val`，将对应的 YOLO 标签文件放入 `extradata/labels/train` 和 `extradata/labels/val`。

Each image needs a matching `.txt` label file with the same base name:

每张图片都需要一个同名 `.txt` 标签文件：

```text
images/train/dog_001.jpg
labels/train/dog_001.txt
```

Label format:

标签格式：

```text
class_id x_center y_center width height
```

Class IDs must follow `extradata/classes.txt`.

类别编号必须严格按照 `extradata/classes.txt` 中的顺序。

Fine-tune from the current large-run model:

从当前大数据集训练得到的最佳模型继续微调：

```powershell
E:\Final_Project_Animal_Counting\.venv\Scripts\python.exe finetune_extra.py --epochs 10 --imgsz 512 --batch 16 --device 0
```

The fine-tuned model will be saved to:

微调后的模型会保存到：

```text
runs/animal_extradata_finetune/weights/best.pt
```

Evaluate with the fine-tuned model by editing `animal_counting.py` to use the
new weight path, or by loading this weight in the inference script you use for
submission.

如果要使用微调后的模型进行预测，可以修改 `animal_counting.py` 中的模型权重路径，或者在提交用的推理脚本中加载这个新的 `best.pt`。

## Validation Format Check / 验证输出格式

The provided validation set includes `ground_truth.json`, so this command creates a
known-correct validation JSON for checking the required output format:

项目提供的验证集包含 `ground_truth.json`，因此可以用下面命令生成并检查预测 JSON 格式：

```powershell
python evaluate.py --image-dir val_set --truth-json val_set\ground_truth.json --output val_predictions.json
python score_predictions.py --truth val_set\ground_truth.json --pred val_predictions.json
```

Do not use `--truth-json` for the final hidden evaluation set. It is only a local
validation shortcut because the validation labels are included in the released files.

最终隐藏测试集不能使用 `--truth-json`。这个参数只用于本地验证，因为已发布的验证数据中包含标准答案标签。
