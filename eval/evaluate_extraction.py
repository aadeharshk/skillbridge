"""Measure skill-extraction precision and recall on hand-labelled lines.

Run:  python -m eval.evaluate_extraction
"""
import json
from pathlib import Path

from matcher.skills import extract_skills

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "eval" / "labelled_lines.json").read_text())


def main():
    tp = fp = fn = 0
    errors = []
    for item in DATA:
        gold, pred = set(item["skills"]), extract_skills(item["text"])
        tp += len(gold & pred)
        fp += len(pred - gold)
        fn += len(gold - pred)
        if gold != pred:
            errors.append({"text": item["text"], "missed": sorted(gold - pred), "extra": sorted(pred - gold)})
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    report = {"n_lines": len(DATA), "n_gold_skills": tp + fn,
              "precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3),
              "errors": errors}
    (ROOT / "eval" / "results.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
