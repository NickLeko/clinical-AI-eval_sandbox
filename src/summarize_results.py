import argparse
import json
import os
from pathlib import Path

import pandas as pd

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.artifact_paths import build_artifact_paths


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def safe_mean(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    return float(series.mean())


def load_run_manifest(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing run manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main(top_n: int, results_dir: str) -> None:
    paths = build_artifact_paths(results_dir)
    if not paths.evaluation_output_path.exists():
        raise FileNotFoundError(f"Missing file: {paths.evaluation_output_path}")

    df = pd.read_csv(paths.evaluation_output_path)
    manifest = load_run_manifest(paths.run_manifest_path)

    for col in ["unsafe_recommendation", "hallucination_suspected", "refusal_failure"]:
        if col not in df.columns:
            df[col] = False
    if "failure_tags" in df.columns:
        df["failure_tags"] = df["failure_tags"].fillna("").astype(str)

    # Safety signal subsets
    unsafe_cases = df[df["unsafe_recommendation"] == True]
    halluc_cases = df[df["hallucination_suspected"] == True]
    refusal_cases = df[df["refusal_failure"] == True]
    
    # Safety signal rates
    unsafe_rate = len(unsafe_cases) / max(len(df), 1)
    halluc_rate = len(halluc_cases) / max(len(df), 1)
    refusal_rate = len(refusal_cases) / max(len(df), 1)


    # Normalize
    for col in ["format_compliance", "citation_validity", "required_citations", "uncertainty_alignment", "faithfulness_proxy"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    total = len(df)
    if total == 0:
        raise ValueError("evaluation_output.csv is empty")

    grade_counts = df["overall_grade"].value_counts(dropna=False).to_dict()

    pass_rate = (df["overall_grade"] == "PASS").mean()
    warn_rate = (df["overall_grade"] == "WARN").mean()
    fail_rate = (df["overall_grade"] == "FAIL").mean()

    metric_means = {
        "faithfulness_proxy": safe_mean(df["faithfulness_proxy"]) if "faithfulness_proxy" in df else 0.0,
        "citation_validity": safe_mean(df["citation_validity"]) if "citation_validity" in df else 0.0,
        "required_citations": safe_mean(df["required_citations"]) if "required_citations" in df else 0.0,
        "uncertainty_alignment": safe_mean(df["uncertainty_alignment"]) if "uncertainty_alignment" in df else 0.0,
        "format_compliance": safe_mean(df["format_compliance"]) if "format_compliance" in df else 0.0,
    }

    # Failure tags
    tags = (
        df["failure_tags"]
        .fillna("")
        .astype(str)
        .str.split("|")
        .explode()
    )
    tags = tags[tags != ""]
    tag_counts = tags.value_counts().to_dict()

    # Worst cases by grade then by faithfulness
    grade_rank = {"FAIL": 0, "WARN": 1, "PASS": 2}
    df["_grade_rank"] = df["overall_grade"].map(grade_rank).fillna(9)
    df_sorted = df.sort_values(
        by=["_grade_rank", "faithfulness_proxy", "case_id"],
        ascending=[True, True, True],
    )

    worst = df_sorted.head(top_n)[
        ["case_id", "category", "risk_level", "model_id", "prompt_version", "overall_grade", "faithfulness_proxy", "uncertainty_alignment", "failure_tags"]
    ]

    lines = []
    lines.append(f"# Clinical AI Evaluation Sandbox — Summary\n")
    lines.append(f"_Published run: `{manifest['provider']}` / `{manifest['model_id']}` / `{manifest['run_id']}`_\n")
    lines.append("\n## Run Identity\n")
    lines.append(f"- Provider: **{manifest['provider']}**\n")
    lines.append(f"- Model: **{manifest['model_id']}**\n")
    lines.append(f"- Run ID: **{manifest['run_id']}**\n")
    lines.append(f"- Prompt version: **{manifest['prompt_version']}**\n")
    lines.append(f"- Cases in published run: **{manifest['case_count']}**\n")
    if manifest.get("source_run_ids"):
        lines.append(f"- Source generation run ids: **{', '.join(manifest['source_run_ids'])}**\n")

    lines.append(f"## Scorecard\n")
    lines.append(f"- Total cases scored: **{total}**\n")
    lines.append(f"- PASS: **{grade_counts.get('PASS', 0)}** ({pct(pass_rate)})\n")
    lines.append(f"- WARN: **{grade_counts.get('WARN', 0)}** ({pct(warn_rate)})\n")
    lines.append(f"- FAIL: **{grade_counts.get('FAIL', 0)}** ({pct(fail_rate)})\n")
    lines.append("\n## Interpretation Guardrail\n")
    lines.append("- This published run is a heuristic benchmark artifact, not evidence of clinical safety or deployment readiness.\n")
    lines.append("- Historical cached generations are stored separately under `results/cache/` and are not the published benchmark set.\n")
    lines.append("\n## Heuristic Signal Rates\n")
    lines.append(f"- Unsafe recommendation rate: **{unsafe_rate:.1%}**\n")
    lines.append(f"- Hallucination suspicion rate: **{halluc_rate:.1%}**\n")
    lines.append(f"- Refusal failure rate: **{refusal_rate:.1%}**\n")
    lines.append(f"\n## Mean metric scores\n")
    for k, v in metric_means.items():
        lines.append(f"- {k}: **{v:.3f}**\n")

    lines.append(f"\n## Failure tag counts\n")
    if not tag_counts:
        lines.append("- (none)\n")
    else:
        for tag, count in sorted(tag_counts.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"- {tag}: **{count}**\n")

    lines.append(f"\n## Worst cases (top {top_n})\n")
    lines.append("| case_id | category | risk | model | prompt | grade | faithfulness | uncertainty | tags |\n")
    lines.append("|---|---|---|---|---|---|---:|---:|---|\n")
    for _, r in worst.iterrows():
        lines.append(
            f"| {r['case_id']} | {r.get('category','')} | {r.get('risk_level','')} | {r.get('model_id','')} | "
            f"{r.get('prompt_version','')} | {r.get('overall_grade','')} | {float(r.get('faithfulness_proxy',0.0)):.3f} | "
            f"{float(r.get('uncertainty_alignment',0.0)):.3f} | {r.get('failure_tags','')} |\n"
        )

    os.makedirs(results_dir, exist_ok=True)
    with paths.summary_output_path.open("w", encoding="utf-8") as f:
        f.write("".join(lines))

    print(f"Wrote: {paths.summary_output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize evaluation results into Markdown.")
    parser.add_argument("--top-n", type=int, default=10, help="Number of worst cases to list.")
    parser.add_argument("--results-dir", default="results", help="Directory containing published artifacts.")
    args = parser.parse_args()

    main(top_n=args.top_n, results_dir=args.results_dir)
