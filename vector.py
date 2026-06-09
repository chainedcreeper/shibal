import faiss
import numpy as np

def build_index(embeddings):
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(np.array(embeddings, dtype="float32"))
    return index
