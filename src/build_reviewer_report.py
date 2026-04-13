import argparse
import csv
import html as html_lib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.artifact_paths import build_artifact_paths


EVALUATION_REQUIRED_COLUMNS = {
    "case_id",
    "run_id",
    "provider",
    "model_id",
    "prompt_version",
    "overall_grade",
    "failure_tags",
}
FLAGGED_REQUIRED_FIELDS = {
    "case_id",
    "model_id",
    "prompt_version",
    "overall_grade",
    "failure_tags",
    "question",
    "provided_context",
    "gold_key_points",
    "gold_key_points_coverage",
    "answer_text",
}
MANIFEST_REQUIRED_FIELDS = {"run_id", "provider", "model_id", "prompt_version"}
OVERLAP_FIELDS = ["model_id", "prompt_version", "overall_grade", "failure_tags"]
GRADE_ORDER = ["PASS", "WARN", "FAIL"]
SCORE_FIELDS = [
    "format_compliance",
    "citation_validity",
    "required_citations",
    "uncertainty_alignment",
    "gold_key_points_coverage",
    "faithfulness_proxy",
]
FLAG_FIELDS = [
    "bogus_citations",
    "hallucination_suspected",
    "unsupported_specificity_suspected",
    "unsafe_recommendation",
    "refusal_failure",
]


@dataclass(frozen=True)
class ReviewerReportData:
    manifest: dict[str, Any]
    evaluation_rows: list[dict[str, str]]
    flagged_cases: list[dict[str, Any]]
    grade_counts: Counter[str]
    failure_tag_counts: Counter[str]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def load_evaluation_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = set(reader.fieldnames or [])
        missing = sorted(EVALUATION_REQUIRED_COLUMNS - fieldnames)
        if missing:
            raise ValueError(f"{path.name} missing required columns: {', '.join(missing)}")

        rows = list(reader)

    if not rows:
        raise ValueError(f"{path.name} is empty")
    return rows


def load_flagged_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path.name} line {line_number}: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"Expected JSON object in {path.name} line {line_number}")
            rows.append(row)
    return rows


def parse_failure_tags(value: Any) -> list[str]:
    return [tag.strip() for tag in str(value or "").split("|") if tag.strip()]


def validate_manifest(manifest: dict[str, Any]) -> None:
    missing = sorted(
        field
        for field in MANIFEST_REQUIRED_FIELDS
        if field not in manifest or str(manifest.get(field, "")).strip() == ""
    )
    if missing:
        raise ValueError(f"run_manifest.json missing required fields: {', '.join(missing)}")


def validate_evaluation_rows(manifest: dict[str, Any], rows: list[dict[str, str]]) -> None:
    validate_manifest(manifest)

    expected_identity = {
        "run_id": str(manifest["run_id"]),
        "provider": str(manifest["provider"]),
        "model_id": str(manifest["model_id"]),
        "prompt_version": str(manifest["prompt_version"]),
    }
    seen_case_ids: set[str] = set()
    evaluation_case_ids: list[str] = []

    for row in rows:
        case_id = str(row.get("case_id", "")).strip()
        if not case_id:
            raise ValueError("evaluation_output.csv contains a row without case_id")
        if case_id in seen_case_ids:
            raise ValueError(f"evaluation_output.csv contains duplicate case_id: {case_id}")
        seen_case_ids.add(case_id)
        evaluation_case_ids.append(case_id)

        for field, expected_value in expected_identity.items():
            actual_value = str(row.get(field, ""))
            if actual_value != expected_value:
                raise ValueError(
                    f"evaluation_output.csv field {field} for {case_id} does not match run_manifest.json: "
                    f"expected {expected_value}, found {actual_value}"
                )

    manifest_case_ids = [str(case_id) for case_id in manifest.get("case_ids", [])]
    if manifest_case_ids and evaluation_case_ids != manifest_case_ids:
        raise ValueError("evaluation_output.csv case order/content does not match run_manifest.json")

    if "case_count" in manifest and len(rows) != int(manifest["case_count"]):
        raise ValueError(
            f"evaluation_output.csv row count does not match run_manifest.json: "
            f"expected {manifest['case_count']}, found {len(rows)}"
        )


def build_flagged_cases(
    evaluation_rows: list[dict[str, str]], flagged_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    evaluation_by_case = {row["case_id"]: row for row in evaluation_rows}
    seen_case_ids: set[str] = set()
    flagged_cases: list[dict[str, Any]] = []

    for index, flagged in enumerate(flagged_rows, start=1):
        missing = sorted(field for field in FLAGGED_REQUIRED_FIELDS if field not in flagged)
        label = str(flagged.get("case_id", f"line {index}"))
        if missing:
            raise ValueError(f"flagged_cases.jsonl row {label} missing required fields: {', '.join(missing)}")

        case_id = str(flagged["case_id"])
        if case_id in seen_case_ids:
            raise ValueError(f"flagged_cases.jsonl contains duplicate case_id: {case_id}")
        seen_case_ids.add(case_id)

        if case_id not in evaluation_by_case:
            raise ValueError(f"flagged_cases.jsonl case_id is not present in evaluation_output.csv: {case_id}")

        evaluation = evaluation_by_case[case_id]
        for field in OVERLAP_FIELDS:
            flagged_value = str(flagged.get(field, ""))
            evaluation_value = str(evaluation.get(field, ""))
            if flagged_value != evaluation_value:
                raise ValueError(
                    f"flagged_cases.jsonl field {field} for {case_id} does not match evaluation_output.csv: "
                    f"expected {evaluation_value}, found {flagged_value}"
                )

        grade = str(flagged.get("overall_grade", ""))
        if grade not in {"WARN", "FAIL"}:
            raise ValueError(f"flagged_cases.jsonl row {case_id} has non-flagged grade: {grade}")

        flagged_cases.append(
            {
                "case_id": case_id,
                "run_id": evaluation.get("run_id", ""),
                "provider": evaluation.get("provider", ""),
                "model_id": flagged.get("model_id", ""),
                "prompt_version": flagged.get("prompt_version", ""),
                "overall_grade": flagged.get("overall_grade", ""),
                "failure_tags": flagged.get("failure_tags", ""),
                "category": evaluation.get("category", ""),
                "risk_level": evaluation.get("risk_level", ""),
                "expected_behavior": evaluation.get("expected_behavior", ""),
                "question": flagged.get("question", ""),
                "provided_context": flagged.get("provided_context", ""),
                "gold_key_points": flagged.get("gold_key_points", ""),
                "answer_text": flagged.get("answer_text", ""),
                "scores": {
                    field: evaluation.get(field, flagged.get(field, ""))
                    for field in SCORE_FIELDS
                    if field in evaluation or field in flagged
                },
                "flags": {field: evaluation.get(field, "") for field in FLAG_FIELDS if field in evaluation},
            }
        )

    return flagged_cases


def load_report_data(results_dir: str = "results") -> ReviewerReportData:
    paths = build_artifact_paths(results_dir)
    manifest = load_json(paths.run_manifest_path)
    evaluation_rows = load_evaluation_rows(paths.evaluation_output_path)
    flagged_rows = load_flagged_rows(paths.flagged_output_path)

    validate_evaluation_rows(manifest, evaluation_rows)
    flagged_cases = build_flagged_cases(evaluation_rows, flagged_rows)

    grade_counts: Counter[str] = Counter(row.get("overall_grade", "") or "(blank)" for row in evaluation_rows)
    failure_tag_counts: Counter[str] = Counter(
        tag for row in evaluation_rows for tag in parse_failure_tags(row.get("failure_tags", ""))
    )

    return ReviewerReportData(
        manifest=manifest,
        evaluation_rows=evaluation_rows,
        flagged_cases=flagged_cases,
        grade_counts=grade_counts,
        failure_tag_counts=failure_tag_counts,
    )


def esc(value: Any) -> str:
    return html_lib.escape(str(value if value is not None else ""), quote=True)


def display_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return ", ".join(f"{key}: {val}" for key, val in value.items())
    return str(value if value is not None else "")


def render_definition_list(items: list[tuple[str, Any]]) -> str:
    parts = ["<dl class=\"kv-list\">"]
    for label, value in items:
        parts.append(f"<dt>{esc(label)}</dt><dd>{esc(display_value(value))}</dd>")
    parts.append("</dl>")
    return "".join(parts)


def ordered_grades(grade_counts: Counter[str]) -> list[str]:
    extras = sorted(grade for grade in grade_counts if grade not in GRADE_ORDER)
    return GRADE_ORDER + extras


def render_grade_distribution(data: ReviewerReportData) -> str:
    total = len(data.evaluation_rows)
    rows = []
    for grade in ordered_grades(data.grade_counts):
        count = data.grade_counts.get(grade, 0)
        pct = (count / total * 100) if total else 0.0
        rows.append(
            f"<tr><th scope=\"row\">{esc(grade)}</th><td>{count}</td><td>{pct:.1f}%</td></tr>"
        )

    return (
        "<table>"
        "<thead><tr><th>Grade</th><th>Cases</th><th>Share</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def render_failure_tag_counts(data: ReviewerReportData) -> str:
    if not data.failure_tag_counts:
        return "<p class=\"muted\">No failure tags were present in evaluation_output.csv.</p>"

    rows = []
    for tag, count in sorted(data.failure_tag_counts.items(), key=lambda item: (-item[1], item[0])):
        rows.append(f"<tr><th scope=\"row\">{esc(tag)}</th><td>{count}</td></tr>")

    return (
        "<table>"
        "<thead><tr><th>Failure tag</th><th>Cases</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def grade_class(grade: Any) -> str:
    normalized = str(grade).strip().lower()
    if normalized in {"pass", "warn", "fail"}:
        return normalized
    return "other"


def render_text_block(title: str, value: Any) -> str:
    return f"<section class=\"text-block\"><h4>{esc(title)}</h4><pre>{esc(display_value(value))}</pre></section>"


def render_case_details(case: dict[str, Any], index: int) -> str:
    overlap_items = [
        ("Model ID", case.get("model_id", "")),
        ("Prompt version", case.get("prompt_version", "")),
        ("Overall grade", case.get("overall_grade", "")),
        ("Failure tags", case.get("failure_tags", "")),
    ]
    context_items = [
        ("Run ID", case.get("run_id", "")),
        ("Provider", case.get("provider", "")),
        ("Category", case.get("category", "")),
        ("Risk level", case.get("risk_level", "")),
        ("Expected behavior", case.get("expected_behavior", "")),
    ]
    score_items = [(field, value) for field, value in case.get("scores", {}).items()]
    flag_items = [(field, value) for field, value in case.get("flags", {}).items()]

    blocks = [
        render_text_block("Question", case.get("question", "")),
        render_text_block("Provided Context", case.get("provided_context", "")),
        render_text_block("Gold Key Points", case.get("gold_key_points", "")),
        render_text_block("Model Answer", case.get("answer_text", "")),
    ]

    return (
        f"<article class=\"case-detail\" id=\"case-detail-{index}\">"
        f"<h3>{esc(case.get('case_id', ''))}</h3>"
        "<div class=\"detail-grid\">"
        "<section><h4>Validated Artifact Overlap</h4>"
        f"{render_definition_list(overlap_items)}</section>"
        "<section><h4>Run And Case Context</h4>"
        f"{render_definition_list(context_items)}</section>"
        "<section><h4>Metric Scores</h4>"
        f"{render_definition_list(score_items)}</section>"
        "<section><h4>Boolean Flags</h4>"
        f"{render_definition_list(flag_items)}</section>"
        "</div>"
        f"{''.join(blocks)}"
        "</article>"
    )


def render_flagged_cases(data: ReviewerReportData) -> str:
    if not data.flagged_cases:
        return "<p class=\"muted\">No WARN or FAIL cases were present in flagged_cases.jsonl.</p>"

    table_rows = []
    detail_panels = []
    for index, case in enumerate(data.flagged_cases):
        filter_text = " ".join(
            str(case.get(field, ""))
            for field in [
                "case_id",
                "overall_grade",
                "failure_tags",
                "category",
                "risk_level",
                "question",
                "expected_behavior",
            ]
        )
        grade = case.get("overall_grade", "")
        table_rows.append(
            "<tr class=\"case-row\" tabindex=\"0\" "
            f"data-target=\"case-detail-{index}\" "
            f"data-grade=\"{esc(grade)}\" "
            f"data-filter-text=\"{esc(filter_text.lower())}\">"
            f"<td><button type=\"button\" class=\"case-button\" data-target=\"case-detail-{index}\">"
            f"{esc(case.get('case_id', ''))}</button></td>"
            f"<td><span class=\"badge {grade_class(grade)}\">{esc(grade)}</span></td>"
            f"<td>{esc(case.get('failure_tags', ''))}</td>"
            f"<td>{esc(case.get('category', ''))}</td>"
            f"<td>{esc(case.get('risk_level', ''))}</td>"
            f"<td>{esc(case.get('expected_behavior', ''))}</td>"
            "</tr>"
        )
        detail_panels.append(render_case_details(case, index))

    return (
        "<div class=\"filters\">"
        "<label for=\"case-filter\">Filter cases</label>"
        "<input id=\"case-filter\" type=\"search\" placeholder=\"case id, tag, grade, category, question\">"
        "<label for=\"grade-filter\">Grade</label>"
        "<select id=\"grade-filter\"><option value=\"\">All grades</option>"
        "<option value=\"WARN\">WARN</option><option value=\"FAIL\">FAIL</option></select>"
        "<span id=\"visible-count\" class=\"muted\"></span>"
        "</div>"
        "<div class=\"review-grid\">"
        "<div class=\"table-wrap\">"
        "<table class=\"flagged-table\">"
        "<thead><tr><th>Case</th><th>Grade</th><th>Failure tags</th><th>Category</th><th>Risk</th>"
        "<th>Expected behavior</th></tr></thead>"
        f"<tbody>{''.join(table_rows)}</tbody>"
        "</table>"
        "</div>"
        f"<div class=\"detail-wrap\">{''.join(detail_panels)}</div>"
        "</div>"
    )


def render_report_html(data: ReviewerReportData) -> str:
    manifest = data.manifest
    total_cases = len(data.evaluation_rows)
    flagged_count = len(data.flagged_cases)
    run_title = f"{manifest.get('provider', '')} / {manifest.get('model_id', '')} / {manifest.get('run_id', '')}"
    summary_items = [
        ("Provider", manifest.get("provider", "")),
        ("Model", manifest.get("model_id", "")),
        ("Run ID", manifest.get("run_id", "")),
        ("Prompt version", manifest.get("prompt_version", "")),
        ("Run kind", manifest.get("run_kind", "")),
        ("Benchmark status", manifest.get("benchmark_status", "")),
        ("Cases in run", manifest.get("case_count", total_cases)),
        ("Dataset total rows", manifest.get("dataset_total_rows", "")),
        ("Full dataset run", manifest.get("is_full_dataset_run", "")),
        ("Dataset SHA-256", manifest.get("dataset_sha256", "")),
        ("Generation modes", manifest.get("generation_modes", "")),
        ("Source run IDs", manifest.get("source_run_ids", "")),
    ]

    css = """
body {
  margin: 0;
  background: #f6f6f6;
  color: #202124;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.45;
}
header {
  background: #ffffff;
  border-bottom: 1px solid #d9d9d9;
  padding: 24px;
}
main {
  max-width: 1180px;
  margin: 0 auto;
  padding: 24px;
}
h1, h2, h3, h4 {
  margin: 0 0 12px;
}
p {
  margin: 0 0 12px;
}
.panel {
  background: #ffffff;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  margin-bottom: 20px;
  padding: 18px;
}
.stats {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  margin-bottom: 20px;
}
.stat {
  background: #ffffff;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  padding: 14px;
}
.stat strong {
  display: block;
  font-size: 1.6rem;
}
.muted {
  color: #5f6368;
}
table {
  border-collapse: collapse;
  width: 100%;
}
th, td {
  border-bottom: 1px solid #e4e4e4;
  padding: 9px 10px;
  text-align: left;
  vertical-align: top;
}
thead th {
  background: #eeeeee;
  font-weight: 700;
}
.kv-list {
  display: grid;
  grid-template-columns: minmax(130px, 210px) 1fr;
  gap: 6px 12px;
  margin: 0;
}
.kv-list dt {
  color: #5f6368;
  font-weight: 700;
}
.kv-list dd {
  margin: 0;
  overflow-wrap: anywhere;
}
.badge {
  border-radius: 6px;
  display: inline-block;
  font-weight: 700;
  padding: 2px 8px;
}
.badge.pass {
  background: #d8f5d0;
}
.badge.warn {
  background: #ffe8a3;
}
.badge.fail {
  background: #ffc9c9;
}
.badge.other {
  background: #e5e5e5;
}
.filters {
  align-items: end;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}
.filters label {
  font-weight: 700;
}
input, select, button {
  border: 1px solid #b8b8b8;
  border-radius: 6px;
  font: inherit;
  padding: 8px 10px;
}
button {
  background: #ffffff;
  cursor: pointer;
}
button:hover {
  background: #eeeeee;
}
.review-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: minmax(0, 0.9fr) minmax(320px, 1.1fr);
}
.table-wrap {
  overflow-x: auto;
}
.case-row {
  cursor: pointer;
}
.case-row:hover,
.case-row[aria-selected="true"] {
  background: #f0f0f0;
}
.case-button {
  width: 100%;
}
.case-detail {
  display: none;
}
.case-detail.active {
  display: block;
}
.detail-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}
.text-block {
  margin-top: 14px;
}
pre {
  background: #f2f2f2;
  border: 1px solid #dedede;
  border-radius: 6px;
  margin: 0;
  overflow-x: auto;
  padding: 12px;
  white-space: pre-wrap;
}
@media (max-width: 900px) {
  main {
    padding: 16px;
  }
  .review-grid {
    grid-template-columns: 1fr;
  }
  .kv-list {
    grid-template-columns: 1fr;
  }
}
"""

    js = """
(function () {
  const textFilter = document.getElementById("case-filter");
  const gradeFilter = document.getElementById("grade-filter");
  const visibleCount = document.getElementById("visible-count");
  const rows = Array.from(document.querySelectorAll(".case-row"));
  const details = Array.from(document.querySelectorAll(".case-detail"));

  function showDetail(targetId) {
    details.forEach((detail) => {
      detail.classList.toggle("active", detail.id === targetId);
    });
    rows.forEach((row) => {
      row.setAttribute("aria-selected", row.dataset.target === targetId ? "true" : "false");
    });
  }

  function visibleRows() {
    return rows.filter((row) => row.style.display !== "none");
  }

  function applyFilters() {
    const query = (textFilter ? textFilter.value : "").trim().toLowerCase();
    const grade = gradeFilter ? gradeFilter.value : "";
    let count = 0;

    rows.forEach((row) => {
      const matchesText = !query || row.dataset.filterText.includes(query);
      const matchesGrade = !grade || row.dataset.grade === grade;
      const show = matchesText && matchesGrade;
      row.style.display = show ? "" : "none";
      if (show) {
        count += 1;
      }
    });

    if (visibleCount) {
      visibleCount.textContent = count + " visible";
    }

    const active = document.querySelector(".case-detail.active");
    const activeRow = active ? rows.find((row) => row.dataset.target === active.id) : null;
    if (!activeRow || activeRow.style.display === "none") {
      const firstVisible = visibleRows()[0];
      if (firstVisible) {
        showDetail(firstVisible.dataset.target);
      } else {
        details.forEach((detail) => detail.classList.remove("active"));
      }
    }
  }

  rows.forEach((row) => {
    row.addEventListener("click", () => showDetail(row.dataset.target));
    row.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        showDetail(row.dataset.target);
      }
    });
  });

  if (textFilter) {
    textFilter.addEventListener("input", applyFilters);
  }
  if (gradeFilter) {
    gradeFilter.addEventListener("change", applyFilters);
  }
  if (rows.length) {
    showDetail(rows[0].dataset.target);
  }
  applyFilters();
})();
"""

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Clinical AI Evaluation Reviewer Report</title>
  <style>{css}</style>
</head>
<body>
  <header>
    <h1>Clinical AI Evaluation Reviewer Report</h1>
    <p class="muted">Derived from run_manifest.json, evaluation_output.csv, and flagged_cases.jsonl. This report does not rescore cases or change canonical artifact meaning.</p>
    <p><strong>{esc(run_title)}</strong></p>
  </header>
  <main>
    <div class="stats">
      <div class="stat"><span>Total cases</span><strong>{total_cases}</strong></div>
      <div class="stat"><span>Flagged cases</span><strong>{flagged_count}</strong></div>
      <div class="stat"><span>WARN</span><strong>{data.grade_counts.get("WARN", 0)}</strong></div>
      <div class="stat"><span>FAIL</span><strong>{data.grade_counts.get("FAIL", 0)}</strong></div>
    </div>
    <section class="panel">
      <h2>Run Summary</h2>
      {render_definition_list(summary_items)}
    </section>
    <section class="panel">
      <h2>Grade Distribution</h2>
      {render_grade_distribution(data)}
    </section>
    <section class="panel">
      <h2>Failure Tag Counts</h2>
      {render_failure_tag_counts(data)}
    </section>
    <section class="panel">
      <h2>Flagged Cases</h2>
      {render_flagged_cases(data)}
    </section>
  </main>
  <script>{js}</script>
</body>
</html>
"""


def main(results_dir: str = "results", output_path: str | None = None) -> Path:
    paths = build_artifact_paths(results_dir)
    destination = Path(output_path) if output_path else paths.reviewer_report_path
    data = load_report_data(results_dir)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_report_html(data), encoding="utf-8")
    print(f"Wrote: {destination}")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build a self-contained HTML reviewer report from published evaluation artifacts."
    )
    parser.add_argument("--results-dir", default="results", help="Directory containing published artifacts.")
    parser.add_argument(
        "--output",
        default=None,
        help="HTML output path. Defaults to reviewer_report.html inside --results-dir.",
    )
    args = parser.parse_args()

    main(results_dir=args.results_dir, output_path=args.output)
