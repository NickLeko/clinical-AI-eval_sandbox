import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.artifact_paths import build_artifact_paths
from src.metrics import evaluate_case, normalize_pipe_list


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def load_run_manifest(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing run manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_public_run(rows: List[Dict[str, Any]], manifest: Dict[str, Any]) -> None:
    if not rows:
        raise ValueError("No public raw generations found. Run generate_answers.py first.")

    expected_run_id = str(manifest["run_id"])
    expected_provider = str(manifest["provider"])
    expected_model_id = str(manifest["model_id"])

    seen_case_ids = set()
    for row in rows:
        if str(row.get("run_id", "")) != expected_run_id:
            raise ValueError(f"Unexpected run_id in public raw generations: {row.get('run_id')}")
        if str(row.get("provider", "")) != expected_provider:
            raise ValueError(f"Unexpected provider in public raw generations: {row.get('provider')}")
        if str(row.get("model_id", "")) != expected_model_id:
            raise ValueError(f"Unexpected model_id in public raw generations: {row.get('model_id')}")

        case_id = str(row.get("case_id", ""))
        if not case_id:
            raise ValueError("Public raw generations are missing case_id values")
        if case_id in seen_case_ids:
            raise ValueError(f"Duplicate case_id in public raw generations: {case_id}")
        seen_case_ids.add(case_id)

    expected_case_count = int(manifest.get("case_count", len(rows)))
    if len(rows) != expected_case_count:
        raise ValueError(
            f"Public raw generations count mismatch: expected {expected_case_count}, found {len(rows)}"
        )


def main(dataset_path: str, results_dir: str) -> None:
    paths = build_artifact_paths(results_dir)
    paths.results_dir.mkdir(parents=True, exist_ok=True)

    # Load dataset
    df_cases = pd.read_csv(dataset_path)
    required_cols = ["case_id", "question", "provided_context", "expected_behavior"]
    for c in required_cols:
        if c not in df_cases.columns:
            raise ValueError(f"Dataset missing required column: {c}")

    # Load generations
    manifest = load_run_manifest(paths.run_manifest_path)
    gen_rows = read_jsonl(paths.public_raw_path)
    validate_public_run(gen_rows, manifest)

    df_gen = pd.DataFrame(gen_rows)

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
        )

        record: Dict[str, Any] = {
            "case_id": row["case_id"],
            "run_id": row.get("run_id", ""),
            "timestamp_utc": row.get("timestamp_utc", ""),
            "provider": row.get("provider", ""),
            "model_id": row.get("model_id", ""),
            "prompt_version": row.get("prompt_version", ""),
            "source_run_id": row.get("source_run_id", ""),
            "generation_mode": row.get("generation_mode", ""),
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
                    "failure_tags": "|".join(metric.failure_tags) if metric.failure_tags else "",
                    "question": row.get("question", ""),
                    "provided_context": row.get("provided_context", ""),
                    "answer_text": row.get("answer_text", ""),
                }
            )

    df_out = pd.DataFrame(out_rows)
    df_out.to_csv(paths.evaluation_output_path, index=False)

    write_jsonl(paths.flagged_output_path, flagged_rows)

    print(f"Wrote: {paths.evaluation_output_path}")
    print(f"Wrote: {paths.flagged_output_path}")
    print("Results dir contents:", sorted(p.name for p in paths.results_dir.iterdir()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run evaluation metrics over generated answers.")
    parser.add_argument("--dataset", default="dataset/clinical_questions.csv", help="Path to dataset CSV.")
    parser.add_argument("--results-dir", default="results", help="Directory containing published artifacts.")
    args = parser.parse_args()

    main(dataset_path=args.dataset, results_dir=args.results_dir)
