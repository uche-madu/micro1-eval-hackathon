from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.grader import grade, summarize  # noqa: E402
from src.reference import production_reference, recognition_reference  # noqa: E402


def load(task_id: str) -> dict:
    return json.loads((ROOT / "tasks" / f"{task_id}.json").read_text())


def modify(raw: str, fn) -> str:
    obj = json.loads(raw)
    fn(obj)
    return json.dumps(obj)


class GraderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.t1 = load("T1")
        self.t2 = load("T2")

    def test_reference_recognition_passes(self) -> None:
        for task in (self.t1, self.t2):
            graded = grade(task, "recognition", recognition_reference(task))
            self.assertEqual(graded["accuracy"], 1.0)
            self.assertEqual(graded["strict"], 1.0)
            self.assertEqual(graded["mean_score"], 1.0)

    def test_reference_production_passes(self) -> None:
        for task in (self.t1, self.t2):
            graded = grade(task, "production", production_reference(task))
            self.assertEqual(graded["accuracy"], 1.0)
            self.assertEqual(graded["strict"], 1.0)
            self.assertEqual(graded["mean_score"], 1.0)
            self.assertEqual(graded["inconsistency_count"], 0)
            self.assertEqual(graded["summary"]["score"], 1.0)

    def test_always_supported_is_rejected(self) -> None:
        raw = modify(
            recognition_reference(self.t1),
            lambda o: [c.update(verdict="SUPPORTED") for c in o["claims"]],
        )
        graded = grade(self.t1, "recognition", raw)
        self.assertLess(graded["accuracy"], 0.5)
        overreach = [r for r in graded["rows"] if r["overreach"]]
        self.assertGreater(len(overreach), 0)

    def test_always_insufficient_is_rejected(self) -> None:
        raw = modify(
            recognition_reference(self.t2),
            lambda o: [c.update(verdict="INSUFFICIENT") for c in o["claims"]],
        )
        graded = grade(self.t2, "recognition", raw)
        self.assertLess(graded["accuracy"], 0.5)

    def test_missing_qualifier_is_caught(self) -> None:
        raw = modify(
            recognition_reference(self.t1),
            lambda o: [c.update(qualifier="") for c in o["claims"] if c["claim_id"] == "C6"],
        )
        graded = grade(self.t1, "recognition", raw)
        row = next(r for r in graded["rows"] if r["id"] == "C6")
        self.assertFalse(row["qualifier_ok"])
        self.assertIn("qualifier_dropped", row["tags"])
        self.assertAlmostEqual(row["score"], 0.9)

    def test_wrong_evidence_is_caught(self) -> None:
        raw = modify(
            recognition_reference(self.t1),
            lambda o: [c.update(evidence_ids=["D12"]) for c in o["claims"] if c["claim_id"] == "C1"],
        )
        graded = grade(self.t1, "recognition", raw)
        row = next(r for r in graded["rows"] if r["id"] == "C1")
        self.assertFalse(row["answer_ok"] is False and row["evidence_kind"] == "exact")
        self.assertIn("evidence_identification", row["tags"])

    def test_superseded_value_is_flagged(self) -> None:
        raw = modify(
            production_reference(self.t1),
            lambda o: [
                i.update(answer="24 months") for i in o["items"] if i["item_id"] == "P1"
            ],
        )
        graded = grade(self.t1, "production", raw)
        row = next(r for r in graded["rows"] if r["id"] == "P1")
        self.assertFalse(row["answer_ok"])
        self.assertTrue(row["overreach"])
        self.assertIn("temporal_overreach", row["tags"])

    def test_unsupported_synthesis_is_flagged(self) -> None:
        raw = modify(
            production_reference(self.t2),
            lambda o: [
                i.update(answer="expired TLS certificate")
                for i in o["items"]
                if i["item_id"] == "P4"
            ],
        )
        graded = grade(self.t2, "production", raw)
        row = next(r for r in graded["rows"] if r["id"] == "P4")
        self.assertTrue(row["overreach"])
        self.assertIn("unsupported_synthesis", row["tags"])

    def test_missing_extra_and_duplicate_items(self) -> None:
        raw = modify(
            production_reference(self.t1),
            lambda o: (
                o["items"].pop(0),
                o["items"].append(
                    {"item_id": "P99", "answer": "yes", "evidence_ids": ["D1"], "qualifier": ""}
                ),
                o["items"].append(dict(o["items"][0])),
            ),
        )
        graded = grade(self.t1, "production", raw)
        self.assertIn("P1", graded["missing"])
        self.assertIn("P99", graded["extras"])
        self.assertTrue(graded["duplicates"])
        self.assertLess(graded["mean_score"], 1.0)

    def test_malformed_json_is_zero(self) -> None:
        graded = grade(self.t1, "production", "{not json")
        self.assertEqual(graded["parse_error"], "invalid_json")
        self.assertEqual(graded["accuracy"], 0.0)

    def test_inconsistent_answers_are_flagged(self) -> None:
        raw = modify(
            production_reference(self.t1),
            lambda o: [
                i.update(answer="24 months") for i in o["items"] if i["item_id"] == "P1"
            ],
        )
        graded = grade(self.t1, "production", raw)
        self.assertGreaterEqual(graded["inconsistency_count"], 1)
        self.assertEqual(graded["inconsistencies"][0]["rule"], "X1")

    def test_summary_forbidden_phrase_is_caught(self) -> None:
        raw = modify(
            production_reference(self.t2),
            lambda o: o.update(
                summary="There was one outage in March, caused by the certificate."
            ),
        )
        graded = grade(self.t2, "production", raw)
        self.assertTrue(graded["summary"]["forbidden_hits"])
        self.assertLess(graded["summary"]["score"], 1.0)

    def test_aggregate_summary(self) -> None:
        records = []
        for task in (self.t1, self.t2):
            for condition, raw in (
                ("recognition", recognition_reference(task)),
                ("production", production_reference(task)),
            ):
                records.append(
                    {
                        "model": "test/model",
                        "condition": condition,
                        "grade": grade(task, condition, raw),
                    }
                )
        summary = summarize(records)
        self.assertEqual(summary["test/model"]["recognition"]["accuracy"], 1.0)
        self.assertEqual(summary["test/model"]["production"]["accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()
