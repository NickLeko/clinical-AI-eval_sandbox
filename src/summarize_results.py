import argparse
import os
from datetime import datetime

import pandas as pd


RESULTS_DIR = "results"
EVAL_IN_PATH = os.path.join(RESULTS_DIR, "evaluation_output.csv")
SUMMARY_OUT_PATH = os.path.join(RESULTS_DIR, "summary.md")


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def safe_mean(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    return float(series.mean())


def main(top_n: int) -> None:
    if not os.path.exists(EVAL_IN_PATH):
        raise FileNotFoundError(f"Missing file: {EVAL_IN_PATH}")

    df = pd.read_csv(EVAL_IN_PATH)

    unsafe_cases = df[df["unsafe_recommendation"] == True]
    halluc_cases = df[df["hallucination_suspected"] == True]
    refusal_cases = df[df["refusal_failure"] == True]

    unsafe_cases = df[df["unsafe_recommendation"] == True]
    halluc_cases = df[df["hallucination_suspected"] == True]
    refusal_cases = df[df["refusal_failure"] == True]

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
    df_sorted = df.sort_values(by=["_grade_rank", "faithfulness_proxy"], ascending=[True, True])

    worst = df_sorted.head(top_n)[
        ["case_id", "category", "risk_level", "model_id", "prompt_version", "overall_grade", "faithfulness_proxy", "uncertainty_alignment", "failure_tags"]
    ]

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines = []
    lines.append(f"# Clinical AI Evaluation Sandbox — Summary\n")
    lines.append(f"_Generated: {now}_\n")
    lines.append(f"## Scorecard\n")
    lines.append(f"- Total cases scored: **{total}**\n")
    lines.append(f"- PASS: **{grade_counts.get('PASS', 0)}** ({pct(pass_rate)})\n")
    lines.append(f"- WARN: **{grade_counts.get('WARN', 0)}** ({pct(warn_rate)})\n")
    lines.append(f"- FAIL: **{grade_counts.get('FAIL', 0)}** ({pct(fail_rate)})\n")
    lines.append("")
    lines.append("## Safety Signals")
    lines.append("")
    lines.append(f"- Unsafe recommendation rate: **{unsafe_rate:.1%}**")
    lines.append(f"- Hallucination suspicion rate: **{halluc_rate:.1%}**")
    lines.append(f"- Refusal failure rate: **{refusal_rate:.1%}**")

    lines.append(f"\n## Mean metric scores\n")
    for k, v in metric_means.items():
        lines.append(f"- {k}: **{v:.3f}**\n")
        
    lines.append(f"\n## Failure tag counts\n")
    if not tag_counts:
        lines.append("- (none)\n")
    else:
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True):
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


    
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(SUMMARY_OUT_PATH, "w", encoding="utf-8") as f:
        f.write("".join(lines))

    print(f"Wrote: {SUMMARY_OUT_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize evaluation results into Markdown.")
    parser.add_argument("--top-n", type=int, default=10, help="Number of worst cases to list.")
    args = parser.parse_args()

    main(top_n=args.top_n)

