from __future__ import annotations

import argparse
import json
from pathlib import Path


def score_sample(truth: dict[str, int], pred: dict[str, int]) -> float:
    if not truth:
        return 0.0
    n = len(truth)
    score = 0.0
    for label, true_count in truth.items():
        if label in pred:
            score += 50.0 / n
            if pred[label] == true_count:
                score += 50.0 / n
    extras = set(pred) - set(truth)
    score -= 5.0 * len(extras)
    return max(score, 0.0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Score predictions with the project rule.")
    parser.add_argument("--truth", required=True)
    parser.add_argument("--pred", required=True)
    args = parser.parse_args()

    truth = json.loads(Path(args.truth).read_text(encoding="utf-8"))
    pred = json.loads(Path(args.pred).read_text(encoding="utf-8"))
    scores = {name: score_sample(labels, pred.get(name, {})) for name, labels in truth.items()}
    mean = sum(scores.values()) / len(scores) if scores else 0.0
    for name, score in sorted(scores.items()):
        print(f"{name}: {score:.2f}")
    print(f"Mean: {mean:.2f}")


if __name__ == "__main__":
    main()
