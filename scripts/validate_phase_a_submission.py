"""Check CP0/Phase A artifacts offline without calling a model or an API."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.report_contracts import (
    validate_answers, validate_markdown, validate_metadata, validate_phase_a,
)


def main():
    answers_path = ROOT / "artifacts/answers_50q.json"
    questions_path = ROOT / "fixtures/test_set_50q.json"
    answers = json.loads(answers_path.read_text(encoding="utf-8"))
    questions = json.loads(questions_path.read_text(encoding="utf-8"))
    report = json.loads((ROOT / "artifacts/ragas_50q.json").read_text(encoding="utf-8"))
    validate_answers(answers, questions)
    assert [row["id"] for row in answers] == [row["id"] for row in questions], "Answer order mismatch"
    validate_phase_a(report, answers)
    validate_metadata(report, [answers_path, questions_path])
    assert [row["question_id"] for row in report["per_question"]] == [row["id"] for row in answers], "Evaluation order mismatch"
    validate_markdown(ROOT / "doc/reports/failure_clusters.md")
    print("CP0/Phase A OK: 50 answers (20/20/10), source fields/order/models preserved")
    print("RAGAS OK: 200 finite metrics, exact bottom 10, matrix/means and source hashes valid")
    print("failure_clusters.md OK: populated report, no placeholders")
    print("Scope: CP0/Phase A; complete team identities, Git evidence and other phases separately")


if __name__ == "__main__":
    main()
