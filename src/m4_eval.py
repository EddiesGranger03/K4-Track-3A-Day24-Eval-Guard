from __future__ import annotations

"""Module 4: RAGAS Evaluation — 4 metrics + failure analysis."""

import os, sys, json, math
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dataclasses import dataclass, asdict, is_dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH, EVALUATION_LLM_MODEL, EVALUATION_EMBEDDING_MODEL


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    """Load test set from JSON. (Đã implement sẵn)"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Run evaluation with explicit evaluator models; fail on missing measurements."""
    metric_names = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
    if not questions or not (len(questions) == len(answers) == len(contexts) == len(ground_truths)):
        raise ValueError("Evaluation requires nonempty inputs of equal length")

    from copy import deepcopy
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
    from datasets import Dataset
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings

    llm = ChatOpenAI(model=EVALUATION_LLM_MODEL, temperature=0)
    embeddings = OpenAIEmbeddings(model=EVALUATION_EMBEDDING_MODEL)
    dataset = Dataset.from_dict({
        "question": questions, "answer": answers,
        "contexts": contexts, "ground_truth": ground_truths,
    })
    result = evaluate(dataset, metrics=deepcopy([
        faithfulness, answer_relevancy, context_precision, context_recall,
    ]), llm=llm, embeddings=embeddings, raise_exceptions=True)
    records = result.to_pandas().to_dict(orient="records")
    if len(records) != len(questions):
        raise ValueError("RAGAS returned an unexpected number of rows")
    per_question = []
    for i, row in enumerate(records):
        if (row["question"] != questions[i] or row["answer"] != answers[i]
                or list(row["contexts"]) != contexts[i] or row["ground_truth"] != ground_truths[i]):
            raise ValueError(f"RAGAS changed input order or content at row {i}")
        scores = {name: float(row[name]) for name in metric_names}
        if any(not math.isfinite(value) or not 0 <= value <= 1 for value in scores.values()):
            raise ValueError(f"RAGAS returned missing or invalid metrics at row {i}")
        per_question.append(EvalResult(
            question=questions[i], answer=answers[i], contexts=list(contexts[i]),
            ground_truth=ground_truths[i], **scores,
        ))
    return {
        **{name: sum(getattr(row, name) for row in per_question) / len(per_question)
           for name in metric_names},
        "per_question": per_question,
        "metadata": {"evaluator_models": [llm.model_name, embeddings.model]},
    }


def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10) -> list[dict]:
    """Analyze bottom-N worst questions using Diagnostic Tree."""
    if bottom_n <= 0:
        return []
    diagnostic_tree = {
        "faithfulness": ("LLM hallucinating", "Tighten system prompt, lower temperature to 0"),
        "context_recall": ("Missing relevant chunks", "Improve chunking or add BM25 keywords"),
        "context_precision": ("Too many irrelevant chunks", "Add Cross-Encoder reranking or metadata filter"),
        "answer_relevancy": ("Answer doesn't match question", "Improve prompt template for direct answers"),
    }
    failures = []
    for result in eval_results:
        scores = {name: getattr(result, name) for name in diagnostic_tree}
        worst_metric = min(scores, key=scores.get)
        diagnosis, suggested_fix = diagnostic_tree[worst_metric]
        failures.append({
            "question": result.question,
            "worst_metric": worst_metric,
            "score": sum(scores.values()) / len(scores),
            "diagnosis": diagnosis,
            "suggested_fix": suggested_fix,
        })
    return sorted(failures, key=lambda item: item["score"])[:bottom_n]


def save_report(results: dict, failures: list[dict], path: str = "reports/ragas_report.json"):
    """Save evaluation report to JSON. (Đã implement sẵn)"""
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    report = {
        "aggregate": {k: v for k, v in results.items() if k != "per_question"},
        "num_questions": len(results.get("per_question", [])),
        "per_question": [asdict(row) if is_dataclass(row) else row
                         for row in results.get("per_question", [])],
        "failures": failures,
    }
    # JSON has no NaN value: retain missing measurements as null, never as zero.
    def json_safe(value):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        if isinstance(value, dict):
            return {key: json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [json_safe(item) for item in value]
        return value

    report = json_safe(report)
    report["status"] = "complete" if report["per_question"] and all(
        row.get(metric) is not None for row in report["per_question"]
        for metric in ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
    ) else "incomplete"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, allow_nan=False)
    print(f"Report saved to {path}")


if __name__ == "__main__":
    test_set = load_test_set()
    print(f"Loaded {len(test_set)} test questions")
    print("Run pipeline.py first to generate answers, then call evaluate_ragas().")
