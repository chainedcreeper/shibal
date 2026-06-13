"""FAISS 인덱스 빌더. IndexFlatIP = inner product = cosine (정규화 임베딩)."""
import faiss
import numpy as np


def build_index(embeddings):
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(np.array(embeddings, dtype="float32"))
    return index
