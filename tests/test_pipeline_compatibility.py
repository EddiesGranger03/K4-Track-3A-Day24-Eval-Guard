"""Regression for the Qdrant 1.9 client used by the lab, without model downloads."""
import numpy as np
import pytest
from qdrant_client import QdrantClient
from src.m2_search import DenseSearch

pytestmark = pytest.mark.support


def test_dense_index_and_search_with_pinned_qdrant_api():
    class Encoder:
        def encode(self, texts, **kwargs):
            if isinstance(texts, str):
                return np.array([1., 0.])
            return np.array([[1., 0.], [0., 1.]])

    dense = DenseSearch.__new__(DenseSearch)
    dense.client = QdrantClient(":memory:")
    dense._encoder = Encoder()
    dense._encoder_failed = False
    try:
        dense.index([{"text": "Leave policy", "metadata": {"source": "leave.md", "parent_id": "p0"}},
                     {"text": "VPN policy", "metadata": {"source": "vpn.md", "parent_id": "p1"}}],
                    collection="regression")
        rows = dense.search("Leave", top_k=1, collection="regression")
        assert len(rows) == 1
        assert rows[0].text == "Leave policy"
        assert rows[0].metadata == {"source": "leave.md", "parent_id": "p0"}
        assert rows[0].method == "dense"
        assert rows[0].score == pytest.approx(1.)
    finally:
        dense.client.close()
