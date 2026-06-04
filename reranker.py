from sentence_transformers import CrossEncoder

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = CrossEncoder("BAAI/bge-reranker-v2-m3")
    return _model


def rerank(query, candidates, top_k=3):
    model = _get_model()
    pairs = [(query, c["text"]) for c in candidates]
    scores = model.predict(pairs)
    ranked = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
    return [c for _, c in ranked[:top_k]]
