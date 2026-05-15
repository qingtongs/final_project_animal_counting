# Extra Fine-tuning Dataset

Put additional manually labeled YOLO-format data here before fine-tuning.

Directory layout:

```text
extradata/
  animal_extradata.yaml
  classes.txt
  images/
    train/
    val/
  labels/
    train/
    val/
```

Rules:

- Each image in `images/train` needs a matching label file in `labels/train`.
- Each image in `images/val` needs a matching label file in `labels/val`.
- Label filenames must match image filenames, for example `dog_001.jpg` and `dog_001.txt`.
- Labels must use YOLO format: `class_id x_center y_center width height`.
- Coordinates must be normalized between 0 and 1.
- Class IDs must follow `classes.txt` exactly.

Example label line:

```text
1 0.5234 0.4812 0.2500 0.3200
```

This means one dog bounding box.
