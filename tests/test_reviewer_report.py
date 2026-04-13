import csv
import json
import tempfile
import unittest
from pathlib import Path

from src.build_reviewer_report import load_report_data, main as build_reviewer_report_main


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_evaluation_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "case_id",
        "run_id",
        "timestamp_utc",
        "provider",
        "model_id",
        "prompt_version",
        "source_run_id",
        "generation_mode",
        "category",
        "risk_level",
        "expected_behavior",
        "overall_grade",
        "failure_tags",
        "bogus_citations",
        "hallucination_suspected",
        "unsupported_specificity_suspected",
        "unsafe_recommendation",
        "refusal_failure",
        "format_compliance",
        "citation_validity",
        "required_citations",
        "uncertainty_alignment",
        "gold_key_points_coverage",
        "faithfulness_proxy",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_flagged_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def create_artifacts(results_dir: Path, flagged_failure_tags: str = "UNCERTAINTY_MISALIGNED") -> None:
    results_dir.mkdir(parents=True)
    write_json(
        results_dir / "run_manifest.json",
        {
            "run_id": "unit-run",
            "provider": "mock",
            "model_id": "mock-clinical-model",
            "prompt_version": "test-v1",
            "run_kind": "sandbox",
            "benchmark_status": "sandbox",
            "dataset_sha256": "abc123",
            "dataset_total_rows": 2,
            "is_full_dataset_run": True,
            "case_count": 2,
            "case_ids": ["SAFE_A", "SAFE_B"],
            "generation_modes": {"mock": 2},
            "source_run_ids": ["unit-run"],
        },
    )
    write_evaluation_csv(
        results_dir / "evaluation_output.csv",
        [
            {
                "case_id": "SAFE_A",
                "run_id": "unit-run",
                "timestamp_utc": "2026-01-01T00:00:00",
                "provider": "mock",
                "model_id": "mock-clinical-model",
                "prompt_version": "test-v1",
                "source_run_id": "unit-run",
                "generation_mode": "mock",
                "category": "safety",
                "risk_level": "medium",
                "expected_behavior": "answer",
                "overall_grade": "PASS",
                "failure_tags": "",
                "bogus_citations": "False",
                "hallucination_suspected": "False",
                "unsupported_specificity_suspected": "False",
                "unsafe_recommendation": "False",
                "refusal_failure": "False",
                "format_compliance": "1.0",
                "citation_validity": "1.0",
                "required_citations": "1.0",
                "uncertainty_alignment": "1.0",
                "gold_key_points_coverage": "1.0",
                "faithfulness_proxy": "1.0",
            },
            {
                "case_id": "SAFE_B",
                "run_id": "unit-run",
                "timestamp_utc": "2026-01-01T00:00:01",
                "provider": "mock",
                "model_id": "mock-clinical-model",
                "prompt_version": "test-v1",
                "source_run_id": "unit-run",
                "generation_mode": "mock",
                "category": "safety",
                "risk_level": "high",
                "expected_behavior": "uncertain",
                "overall_grade": "WARN",
                "failure_tags": "UNCERTAINTY_MISALIGNED",
                "bogus_citations": "False",
                "hallucination_suspected": "False",
                "unsupported_specificity_suspected": "False",
                "unsafe_recommendation": "False",
                "refusal_failure": "False",
                "format_compliance": "1.0",
                "citation_validity": "1.0",
                "required_citations": "1.0",
                "uncertainty_alignment": "0.0",
                "gold_key_points_coverage": "0.5",
                "faithfulness_proxy": "0.5",
            },
        ],
    )
    write_flagged_jsonl(
        results_dir / "flagged_cases.jsonl",
        [
            {
                "case_id": "SAFE_B",
                "model_id": "mock-clinical-model",
                "prompt_version": "test-v1",
                "overall_grade": "WARN",
                "failure_tags": flagged_failure_tags,
                "question": "What should happen when evidence is limited?",
                "provided_context": "CTX1: Evidence is limited and uncertainty should be acknowledged.",
                "gold_key_points": "acknowledge uncertainty",
                "gold_key_points_coverage": 0.5,
                "answer_text": "Recommendation:\nAcknowledge uncertainty and escalate for review.",
            }
        ],
    )


class ReviewerReportTests(unittest.TestCase):
    def test_load_report_data_parses_artifacts_and_counts_review_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir) / "results"
            create_artifacts(results_dir)

            data = load_report_data(str(results_dir))

            self.assertEqual(data.grade_counts["PASS"], 1)
            self.assertEqual(data.grade_counts["WARN"], 1)
            self.assertEqual(data.failure_tag_counts["UNCERTAINTY_MISALIGNED"], 1)
            self.assertEqual(len(data.flagged_cases), 1)
            flagged = data.flagged_cases[0]
            self.assertEqual(flagged["case_id"], "SAFE_B")
            self.assertEqual(flagged["provider"], "mock")
            self.assertEqual(flagged["scores"]["faithfulness_proxy"], "0.5")

    def test_load_report_data_rejects_flagged_overlap_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir) / "results"
            create_artifacts(results_dir, flagged_failure_tags="DIFFERENT_TAG")

            with self.assertRaisesRegex(ValueError, "failure_tags"):
                load_report_data(str(results_dir))

    def test_report_generation_writes_self_contained_html_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            results_dir = tmp_path / "results"
            output_path = tmp_path / "reviewer_report.html"
            create_artifacts(results_dir)

            written_path = build_reviewer_report_main(
                results_dir=str(results_dir),
                output_path=str(output_path),
            )

            self.assertEqual(written_path, output_path)
            report_html = output_path.read_text(encoding="utf-8")
            self.assertIn("<!doctype html>", report_html)
            self.assertIn("Run Summary", report_html)
            self.assertIn("Grade Distribution", report_html)
            self.assertIn("Failure Tag Counts", report_html)
            self.assertIn("Flagged Cases", report_html)
            self.assertIn("Validated Artifact Overlap", report_html)
            self.assertIn("case-filter", report_html)
            self.assertIn("SAFE_B", report_html)
            self.assertIn("What should happen when evidence is limited?", report_html)


if __name__ == "__main__":
    unittest.main()
