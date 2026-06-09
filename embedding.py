import os
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")

from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-m3", local_files_only=True)

def create_embeddings(chunks):
    return model.encode(chunks, normalize_embeddings=True)
