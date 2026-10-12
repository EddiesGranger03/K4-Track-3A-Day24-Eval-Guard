"""Offline contract checks; live model/API validation is a separate setup step."""
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src import m1_chunking, m2_search, m4_eval, m5_enrichment

pytestmark = pytest.mark.support


def test_chunk_enrichment_preserves_source_and_order(monkeypatch):
    monkeypatch.setattr(m5_enrichment, "OPENAI_API_KEY", "")
    chunks = []
    for source in ("policy_old.md", "policy_new.md"):
        parents, children = m1_chunking.chunk_hierarchical(
            "First policy sentence. Second policy sentence.",
            parent_size=30, child_size=20, metadata={"source": source},
        )
        parent_ids = {parent.parent_id for parent in parents}
        for child in children:
            assert child.parent_id in parent_ids
            assert child.metadata["source"] == source
            chunks.append({"text": child.text, "metadata": {
                **child.metadata, "parent_id": child.parent_id,
            }})
    enriched = m5_enrichment.enrich_chunks(chunks)
    assert len(enriched) == len(chunks)
    for original, result in zip(chunks, enriched):
        assert result.original_text == original["text"]
        assert original["text"] in result.enriched_text
        for key, value in original["metadata"].items():
            assert result.auto_metadata[key] == value


def test_dense_search_uses_qdrant_19_api_and_keeps_metadata():
    search = m2_search.DenseSearch.__new__(m2_search.DenseSearch)
    search._encoder = Mock()
    search._encoder.encode.return_value.tolist.return_value = [0.1, 0.2]
    search.client = Mock(spec=["search"])
    search.client.search.return_value = [SimpleNamespace(
        score=0.8, payload={"text": "Policy", "source": "policy.md", "parent_id": "p1"},
    )]
    results = search.search("Question", top_k=3)
    search.client.search.assert_called_once_with(
        m2_search.COLLECTION_NAME, query_vector=[0.1, 0.2], limit=3,
    )
    assert results[0].text == "Policy"
    assert results[0].score == 0.8
    assert results[0].metadata["source"] == "policy.md"
    assert results[0].metadata["parent_id"] == "p1"


@pytest.fixture
def evaluator(monkeypatch):
    row = dict(question="Q", answer="A", contexts=["C"], ground_truth="GT",
               faithfulness=0.8, answer_relevancy=0.7, context_precision=0.6, context_recall=0.5)
    evaluate = Mock()
    evaluate.return_value.to_pandas.return_value.to_dict.return_value = [row]
    monkeypatch.setitem(sys.modules, "ragas", SimpleNamespace(evaluate=evaluate))
    monkeypatch.setitem(sys.modules, "ragas.metrics", SimpleNamespace(**{
        name: object() for name in ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
    }))
    monkeypatch.setitem(sys.modules, "datasets", SimpleNamespace(Dataset=SimpleNamespace(from_dict=lambda data: data)))
    monkeypatch.setitem(sys.modules, "langchain_openai", SimpleNamespace(
        ChatOpenAI=lambda model, temperature: SimpleNamespace(model_name=model),
        OpenAIEmbeddings=lambda model: SimpleNamespace(model=model),
    ))
    return evaluate, row


def test_evaluation_records_models_passed_to_ragas(evaluator):
    evaluate, _ = evaluator
    result = m4_eval.evaluate_ragas(["Q"], ["A"], [["C"]], ["GT"])
    arguments = evaluate.call_args.kwargs
    assert result["metadata"]["evaluator_models"] == [
        arguments["llm"].model_name, arguments["embeddings"].model,
    ]
    assert result["per_question"][0].faithfulness == 0.8
    assert arguments["raise_exceptions"] is True


@pytest.mark.parametrize("change", [{"faithfulness": float("nan")}, {"context_recall": 1.1}, {"question": "Reordered"}])
def test_evaluation_rejects_invalid_evidence(evaluator, change):
    _, row = evaluator
    row.update(change)
    with pytest.raises(ValueError):
        m4_eval.evaluate_ragas(["Q"], ["A"], [["C"]], ["GT"])


def test_evaluation_propagates_api_failure(evaluator):
    evaluate, _ = evaluator
    evaluate.side_effect = RuntimeError("API unavailable")
    with pytest.raises(RuntimeError, match="API unavailable"):
        m4_eval.evaluate_ragas(["Q"], ["A"], [["C"]], ["GT"])
