from __future__ import annotations

"""Phase A: RAGAS Production Evaluation — 50q, 3 distributions, cluster analysis."""

import json
import math
from collections.abc import Mapping
import os
import sys
from dataclasses import asdict, dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH, ANSWERS_PATH, ARTIFACTS_DIR
from src.experiment_support import write_json

Distribution = str  # "factual" | "multi_hop" | "adversarial"

DIAGNOSTIC_TREE = {
    "faithfulness":      ("Có thể có claim chưa được contexts hỗ trợ; cần đối chiếu từng claim", "Ràng buộc generation theo nguồn và gắn citation cho từng claim"),
    "context_recall":    ("Contexts có thể thiếu dữ kiện trong reference", "Mở rộng retrieval theo từng ý hỏi và ghép context từ nhiều nguồn"),
    "context_precision": ("Contexts có thể chứa đoạn ít liên quan hoặc sai phiên bản", "Đa dạng hóa nguồn sau rerank và lọc metadata theo hiệu lực chính sách"),
    "answer_relevancy":  ("Câu trả lời có thể chưa bao phủ đúng trọng tâm câu hỏi", "Tách các ý cần trả lời trong prompt và kiểm tra phủ định/điều kiện"),
}


@dataclass
class RagasResult:
    question_id: int
    distribution: Distribution
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float

    @property
    def avg_score(self) -> float:
        return (self.faithfulness + self.answer_relevancy +
                self.context_precision + self.context_recall) / 4

    @property
    def worst_metric(self) -> str:
        scores = {
            "faithfulness":      self.faithfulness,
            "answer_relevancy":  self.answer_relevancy,
            "context_precision": self.context_precision,
            "context_recall":    self.context_recall,
        }
        return min(scores, key=scores.get)


# ─── Đã implement sẵn ────────────────────────────────────────────────────────

@dataclass
class RagasEvaluation:
    """Task 2 output: measured rows plus model identifiers reported by m4."""
    results: list[RagasResult]
    evaluator_models: list[str]

def load_test_set_50q(path: str = TEST_SET_PATH) -> list[dict]:
    """Load 50q test set với 3 distributions."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_answers(path: str = ANSWERS_PATH) -> list[dict]:
    """Load pre-generated answers từ setup_answers.py."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"answers_50q.json không tìm thấy tại {path}\n"
            "→ Chạy trước: python scripts/setup_answers.py --live"
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_phase_a_report(results: list[RagasResult], clusters: dict, bottom: list[dict]) -> dict:
    """Provided exporter: preserve the student-produced Task 3 rows verbatim."""
    per_dist: dict[str, dict] = {}
    for dist in ["factual", "multi_hop", "adversarial"]:
        subset = [r for r in results if r.distribution == dist]
        if subset:
            per_dist[dist] = {
                "count": len(subset),
                "faithfulness":      sum(r.faithfulness for r in subset) / len(subset),
                "answer_relevancy":  sum(r.answer_relevancy for r in subset) / len(subset),
                "context_precision": sum(r.context_precision for r in subset) / len(subset),
                "context_recall":    sum(r.context_recall for r in subset) / len(subset),
                "avg_score":         sum(r.avg_score for r in subset) / len(subset),
            }

    report = {
        "total_questions": len(results),
        "per_question": [asdict(r) for r in results],
        "per_distribution": per_dist,
        "failure_clusters": clusters,
        "bottom_10": bottom,
    }
    return report


def save_phase_a_report(results: list[RagasResult], clusters: dict, bottom: list[dict],
                        path: str = os.path.join(ARTIFACTS_DIR, "ragas_50q.json")) -> None:
    write_json(path, build_phase_a_report(results, clusters, bottom))



# ─── Tasks 1-4: Sinh viên implement ──────────────────────────────────────────

DISTRIBUTIONS = ("factual", "multi_hop", "adversarial")
METRICS = tuple(DIAGNOSTIC_TREE)


def group_by_distribution(test_set: list[dict]) -> dict[str, list[dict]]:
    """Group rows without changing their order or source fields."""
    groups = {distribution: [] for distribution in DISTRIBUTIONS}
    for item in test_set:
        distribution = item["distribution"]
        if distribution not in groups:
            raise ValueError(f"Unknown distribution: {distribution!r}")
        groups[distribution].append(item)
    return groups


def run_ragas_50q(answers: list[dict]) -> RagasEvaluation:
    """Adapt actual evaluator measurements; reject missing or invalid scores."""
    from src.m4_eval import evaluate_ragas
    from src.experiment_support import model_ids

    raw = evaluate_ragas(*([row[field] for row in answers] for field in
                          ("question", "answer", "contexts", "ground_truth")))
    if raw.get("evaluation_status", "completed") != "completed":
        raise ValueError("RAGAS evaluation is incomplete; no fabricated scores are accepted")
    per_question = raw.get("per_question", [])
    if len(per_question) != len(answers):
        raise ValueError("Evaluator row count must equal input row count")
    models = raw.get("metadata", {}).get("evaluator_models")
    model_ids(models, "evaluator models")
    if not models:
        raise ValueError("Evaluator must report the models actually used")
    results = []
    for answer, metrics in zip(answers, per_question):
        scores = {}
        for metric in METRICS:
            value = metrics[metric] if isinstance(metrics, Mapping) else getattr(metrics, metric)
            if isinstance(value, bool):
                raise ValueError(f"Question {answer['id']}: boolean {metric}")
            try:
                score = float(value)
            except (TypeError, ValueError) as error:
                raise ValueError(f"Question {answer['id']}: invalid {metric}") from error
            if not math.isfinite(score) or not 0 <= score <= 1:
                raise ValueError(f"Question {answer['id']}: {metric} must be finite in [0,1]")
            scores[metric] = score
        results.append(RagasResult(
            question_id=answer["id"], distribution=answer["distribution"],
            question=answer["question"], answer=answer["answer"],
            contexts=answer["contexts"], ground_truth=answer["ground_truth"], **scores))
    return RagasEvaluation(results, models)


def bottom_10(results: list[RagasResult]) -> list[dict]:
    """Keep precise averages and stable input order when scores tie."""
    rows = []
    for rank, result in enumerate(sorted(results, key=lambda row: row.avg_score)[:10], 1):
        diagnosis, fix = DIAGNOSTIC_TREE[result.worst_metric]
        rows.append({"rank": rank, "question_id": result.question_id,
                     "distribution": result.distribution, "question": result.question,
                     "avg_score": result.avg_score, "worst_metric": result.worst_metric,
                     "diagnosis": diagnosis, "suggested_fix": fix})
    return rows


def cluster_analysis(results: list[RagasResult]) -> dict:
    """Count weakest metrics and select the lowest mean distribution."""
    matrix = {metric: {distribution: 0 for distribution in DISTRIBUTIONS} for metric in METRICS}
    for result in results:
        if result.distribution not in DISTRIBUTIONS:
            raise ValueError(f"Unknown distribution: {result.distribution}")
        matrix[result.worst_metric][result.distribution] += 1
    means = {distribution: sum(row.avg_score for row in results if row.distribution == distribution)
             / sum(row.distribution == distribution for row in results)
             for distribution in DISTRIBUTIONS if any(row.distribution == distribution for row in results)}
    weakest = min(means, key=means.get) if means else None
    dominant_metric = max(METRICS, key=lambda metric: sum(matrix[metric].values())) if results else None
    insight = (f"Nhóm {weakest} có mean thấp nhất ({means[weakest]:.4f}). "
               f"{dominant_metric} là worst_metric của {sum(matrix[dominant_metric].values())}/{len(results)} câu. "
               f"{DIAGNOSTIC_TREE[dominant_metric][1]}. Matrix đếm mọi câu, không đồng nghĩa tất cả đều lỗi."
               if results else "Chưa có kết quả đo để kết luận nhóm yếu.")
    return {"matrix": matrix, "distribution_avg_scores": means,
            "dominant_failure_distribution": weakest,
            "dominant_failure_metric": dominant_metric, "insight": insight}


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from scripts.run_experiments import main
    raise SystemExit(main(["--phase", "a", *sys.argv[1:]]))
