from __future__ import annotations

"""Module 4: RAGAS Evaluation — 4 metrics + failure analysis."""

import json
import hashlib
from pathlib import Path
import math
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dataclasses import asdict, dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float | None
    answer_relevancy: float | None
    context_precision: float | None
    context_recall: float | None


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    """Load test set from JSON. (Đã implement sẵn)"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Measure four RAGAS metrics, checkpoint real rows, fail on missing scores."""
    from config import OPENAI_API_KEY, GENERATION_MODEL, ROOT_DIR
    if not (len(questions) == len(answers) == len(contexts) == len(ground_truths)):
        raise ValueError("RAGAS inputs must have equal lengths")
    if not questions:
        raise ValueError("RAGAS requires nonempty inputs")
    from datasets import Dataset
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
    keys = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
    llm_model = os.getenv("EVALUATOR_LLM_MODEL", GENERATION_MODEL)
    embedding_model = os.getenv("EVALUATOR_EMBEDDING_MODEL", "text-embedding-3-small")
    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    common = {"api_key": OPENAI_API_KEY} if OPENAI_API_KEY else {}
    if base_url:
        common["base_url"] = base_url

    try:
        llm = ChatOpenAI(model=llm_model, temperature=0, timeout=90, max_retries=2,
                         max_tokens=2048, **common)
    except TypeError:
        llm = ChatOpenAI(model=llm_model, temperature=0)
    try:
        embeddings = OpenAIEmbeddings(model=embedding_model, check_embedding_ctx_length=False,
                                      request_timeout=90, max_retries=2, **common)
    except TypeError:
        embeddings = OpenAIEmbeddings(model=embedding_model)
    models = [llm.model_name, embeddings.model]
    inputs = [{"question": q, "answer": a, "contexts": c, "ground_truth": gt}
              for q, a, c, gt in zip(questions, answers, contexts, ground_truths)]
    digest = hashlib.sha256(json.dumps(["ragas-0.1.22-v1", models, base_url, inputs],
                                       ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    cache = Path(ROOT_DIR) / ".cache" / "ragas" / (digest + ".json")
    use_cache = bool(OPENAI_API_KEY) and os.getenv("RAGAS_REFRESH") != "1"
    measured = json.loads(cache.read_text()) if use_cache and cache.exists() else {}
    for attempt in range(3):
        pending = [i for i in range(len(inputs)) if str(i) not in measured]
        if not pending:
            break
        for offset in range(0, len(pending), 10):
            indices = pending[offset:offset + 10]
            print(f"RAGAS attempt {attempt+1}: measuring rows {[i+1 for i in indices]}", flush=True)
            batch = [inputs[i] for i in indices]
            dataset = Dataset.from_dict({key: [row[key] for row in batch] for key in
                                         ("question", "answer", "contexts", "ground_truth")})
            result = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
                              llm=llm, embeddings=embeddings, raise_exceptions=True)
            frame = result.to_pandas()
            try:
                records = frame.to_dict(orient="records")
            except TypeError:
                records = frame.to_dict()
            if len(records) != len(indices):
                raise ValueError("RAGAS returned the wrong row count")
            for index, row in zip(indices, records):
                source = inputs[index]
                if (row.get("question") != source["question"] or row.get("answer") != source["answer"]
                        or list(row.get("contexts", [])) != source["contexts"]
                        or row.get("ground_truth") != source["ground_truth"]):
                    raise ValueError(f"RAGAS changed input order or content at row {index+1}")
                scores = {key: float(row[key]) for key in keys}
                if all(math.isfinite(value) and 0 <= value <= 1 for value in scores.values()):
                    measured[str(index)] = scores
                else:
                    print(f"RAGAS row {index+1}: invalid metric; retry required", flush=True)
            if OPENAI_API_KEY:
                cache.parent.mkdir(parents=True, exist_ok=True)
                cache.write_text(json.dumps(measured, ensure_ascii=False, allow_nan=False))
    missing = [i+1 for i in range(len(inputs)) if str(i) not in measured]
    if missing:
        raise ValueError(f"RAGAS has no complete finite metrics for rows {missing}; real measured rows cached")
    rows = [EvalResult(**item, **measured[str(i)]) for i, item in enumerate(inputs)]
    return {**{key: sum(getattr(row, key) for row in rows)/len(rows) for key in keys},
            "per_question": rows, "evaluation_status": "completed",
            "metadata": {"evaluator_models": models}}


def _safe_float(value) -> float:
    try:
        number = float(value)
        return number if math.isfinite(number) else 0.0
    except (TypeError, ValueError):
        return 0.0


def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 5) -> list[dict]:
    """Analyze bottom-N worst questions using Diagnostic Tree."""
    if bottom_n <= 0:
        return []
    diagnostic_tree = {
        "faithfulness": ("Answer may contain claims unsupported by retrieved context",
                         "Constrain generation to cited context and remove unsupported details"),
        "context_recall": ("Retrieved context is missing relevant facts",
                           "Improve chunk boundaries, query coverage, and hybrid retrieval"),
        "context_precision": ("Retrieved context contains distracting or irrelevant chunks",
                              "Rerank candidates and apply source or metadata filters"),
        "answer_relevancy": ("Answer does not directly address the user question",
                             "Tighten the answer prompt and preserve question intent"),
    }
    def value(item, key):
        return item.get(key, 0.0) if isinstance(item, dict) else getattr(item, key, 0.0)

    records = []
    for item in eval_results:
        values = {key: _safe_float(value(item, key)) for key in diagnostic_tree}
        worst = min(values, key=values.get)
        diagnosis, fix = diagnostic_tree[worst]
        avg = sum(values.values()) / len(values)
        records.append({"question": value(item, "question") or "", "answer": value(item, "answer") or "",
                        "contexts": value(item, "contexts") or [], "ground_truth": value(item, "ground_truth") or "",
                        "average_score": avg, "worst_metric": worst, "score": values[worst],
                        "diagnosis": diagnosis, "suggested_fix": fix,
                        "diagnostic_tree": {"output_correct": "Review answer against ground truth",
                                            "context_relevant": "Review contexts for supporting evidence",
                                            "retrieval_issue": worst in {"context_recall", "context_precision"},
                                            "next_action": fix}})
    return sorted(records, key=lambda record: (record["average_score"], record["score"]))[:bottom_n]


def save_report(results: dict, failures: list[dict], path: str = "reports/ragas_report.json"):
    """Save evaluation report to JSON. (Đã implement sẵn)"""
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    report = {
        "aggregate": {k: v for k, v in results.items() if k not in {"per_question", "run_metadata"}},
        "num_questions": len(results.get("per_question", [])),
        "failures": failures,
        "per_question": [asdict(item) if isinstance(item, EvalResult) else item
                         for item in results.get("per_question", [])],
        "run_metadata": results.get("run_metadata", {}),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Report saved to {path}")


if __name__ == "__main__":
    test_set = load_test_set()
    print(f"Loaded {len(test_set)} test questions")
    print("Run pipeline.py first to generate answers, then call evaluate_ragas().")
