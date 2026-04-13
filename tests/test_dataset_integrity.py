import csv
import re
import unittest
from pathlib import Path


DATASET_PATH = Path(__file__).resolve().parents[1] / "dataset" / "clinical_questions.csv"
ALLOWED_EXPECTED_BEHAVIORS = {"answer", "uncertain", "refuse"}
REQUIRED_COLUMNS = {
    "case_id",
    "category",
    "risk_level",
    "question",
    "provided_context",
    "expected_behavior",
    "required_citations",
    "forbidden_actions",
    "gold_key_points",
    "notes",
}
NON_EMPTY_BENCHMARK_FIELDS = (
    "case_id",
    "category",
    "risk_level",
    "question",
    "provided_context",
    "expected_behavior",
)
CONTEXT_ANCHOR_PATTERN = re.compile(r"\b(CTX\d+):")


def load_dataset_rows() -> list[dict[str, str]]:
    with DATASET_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    missing = REQUIRED_COLUMNS.difference(reader.fieldnames or [])
    if missing:
        raise AssertionError(f"Dataset missing required columns: {sorted(missing)}")
    if not rows:
        raise AssertionError("Dataset has no rows")

    return rows


def pipe_values(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split("|") if part.strip()]


class CheckedInDatasetIntegrityTests(unittest.TestCase):
    def test_case_ids_are_unique(self) -> None:
        rows = load_dataset_rows()
        case_ids = [row["case_id"].strip() for row in rows]

        self.assertEqual(len(case_ids), len(set(case_ids)))

    def test_expected_behavior_values_are_allowed(self) -> None:
        rows = load_dataset_rows()

        for row in rows:
            self.assertIn(row["expected_behavior"].strip(), ALLOWED_EXPECTED_BEHAVIORS, row["case_id"])

    def test_required_benchmark_fields_are_non_empty(self) -> None:
        rows = load_dataset_rows()

        for row in rows:
            for field in NON_EMPTY_BENCHMARK_FIELDS:
                self.assertTrue(row[field].strip(), f"{row.get('case_id', '<missing>')} has empty {field}")

    def test_required_citation_anchors_exist_in_provided_context(self) -> None:
        rows = load_dataset_rows()

        for row in rows:
            context_anchors = set(CONTEXT_ANCHOR_PATTERN.findall(row["provided_context"]))
            for citation in pipe_values(row["required_citations"]):
                self.assertIn(citation, context_anchors, row["case_id"])


if __name__ == "__main__":
    unittest.main()
