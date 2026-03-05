import argparse
import json
import os
from typing import Any, Dict, List

import pandas as pd

from src.metrics import evaluate_case, normalize_pipe_list

RESULTS_DIR = "results"
RAW_IN_PATH = os.path.join(RESULTS_DIR, "raw_generations.jsonl")
EVAL_OUT_PATH = os.path.join(RESULTS_DIR, "evaluation_output.csv")
FLAGGED_OUT_PATH = os.path.join(RESULTS_DIR, "flagged_cases.jsonl")


def read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")

    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main(dataset_path: str, max_ctx_anchors: int) -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Load dataset
    df_cases = pd.read_csv(dataset_path)
    required_cols = ["case_id", "question", "provided_context", "expected_behavior"]
    for c in required_cols:
        if c not in df_cases.columns:
            raise ValueError(f"Dataset missing required column: {c}")

    # Load generations
    gen_rows = read_jsonl(RAW_IN_PATH)
    df_gen = pd.DataFrame(gen_rows)
    if df_gen.empty:
        raise ValueError("No generations found. Run generate_answers.py first.")

    # Ensure expected generation columns exist
    for c in ["case_id", "answer_text"]:
        if c not in df_gen.columns:
            raise ValueError(f"Generations missing required field: {c}")

    # Merge (supports multiple runs/models per case)
    df = df_gen.merge(df_cases, on="case_id", how="left", suffixes=("", "_case"))

    # Guardrail: all generations must match a dataset case
    if df["question"].isna().any():
        missing = df[df["question"].isna()]["case_id"].unique().tolist()
        raise ValueError(f"Some generations have case_id not in dataset: {missing}")

    out_rows: List[Dict[str, Any]] = []
    flagged_rows: List[Dict[str, Any]] = []

    for _, row in df.iterrows():
        required_cits = normalize_pipe_list(row.get("required_citations", ""))
        forbidden_actions = normalize_pipe_list(row.get("forbidden_actions", ""))
        expected_behavior = str(row.get("expected_behavior", "")).strip()

        metric = evaluate_case(
            answer_text=str(row.get("answer_text", "")),
            provided_context=str(row.get("provided_context", "")),
            expected_behavior=expected_behavior,
            required_citations=required_cits,
            forbidden_actions=forbidden_actions,
            max_ctx_anchors=max_ctx_anchors,
        )

        record: Dict[str, Any] = {
            "case_id": row["case_id"],
            "run_id": row.get("run_id", ""),
            "timestamp_utc": row.get("timestamp_utc", ""),
            "provider": row.get("provider", ""),
            "model_id": row.get("model_id", ""),
            "prompt_version": row.get("prompt_version", ""),
            "category": row.get("category", ""),
            "risk_level": row.get("risk_level", ""),
            "expected_behavior": expected_behavior,
            "overall_grade": metric.scores.get("overall_grade", ""),
            "failure_tags": "|".join(metric.failure_tags) if metric.failure_tags else "",
        }

        # Add boolean flags
        for k, v in metric.flags.items():
            record[k] = v

        # Add numeric scores (exclude overall_grade to avoid duplicate)
        for k, v in metric.scores.items():
            if k == "overall_grade":
                continue
            record[k] = v

        out_rows.append(record)

        if record["overall_grade"] in ("FAIL", "WARN"):
            flagged_rows.append(
                {
                    "case_id": row["case_id"],
                    "model_id": row.get("model_id", ""),
                    "prompt_version": row.get("prompt_version", ""),
                    "overall_grade": record["overall_grade"],
                    "failure_tags": record["failure_tags"],
                    "question": row.get("question", ""),
                    "provided_context": row.get("provided_context", ""),
                    "answer_text": row.get("answer_text", ""),
                }
            )

    df_out = pd.DataFrame(out_rows)
    df_out.to_csv(EVAL_OUT_PATH, index=False)

    write_jsonl(FLAGGED_OUT_PATH, flagged_rows)

    print(f"Wrote: {EVAL_OUT_PATH}")
    print(f"Wrote: {FLAGGED_OUT_PATH}")
    print("Results dir contents:", os.listdir(RESULTS_DIR))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run evaluation metrics over generated answers.")
    parser.add_argument("--dataset", default="dataset/clinical_questions.csv", help="Path to dataset CSV.")
    parser.add_argument(
        "--max-ctx-anchors",
        type=int,
        default=8,
        help="Highest allowed CTX anchor number (e.g., 8 allows [CTX1]..[CTX8]).",
    )
    args = parser.parse_args()

    main(dataset_path=args.dataset, max_ctx_anchors=args.max_ctx_anchors)
