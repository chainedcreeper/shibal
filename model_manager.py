import os
import subprocess
import requests

MODELS_DIR = "personal_models"
OLLAMA_URL = "http://localhost:11434"


def personal_model_name(student_id):
    return f"personal_{student_id}"


def personal_model_exists(student_id):
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        models = [m["name"] for m in resp.json().get("models", [])]
        return personal_model_name(student_id) in models
    except Exception:
        return False


def register_personal_model(student_id, gguf_path):
    model_dir = os.path.join(MODELS_DIR, student_id)
    os.makedirs(model_dir, exist_ok=True)

    modelfile_path = os.path.join(model_dir, "Modelfile")
    with open(modelfile_path, "w", encoding="utf-8") as f:
        f.write(f"FROM {os.path.abspath(gguf_path)}\n")
        f.write('SYSTEM "너는 개인화된 대학 강의 AI Tutor다. 이 학생의 수준과 패턴에 맞게 답변하라."\n')

    subprocess.run(
        ["ollama", "create", personal_model_name(student_id), "-f", modelfile_path],
        check=True,
    )


def ask_personal(student_id, context, question):
    import json
    prompt = f"문서:\n{context}\n\n질문: {question}"
    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": personal_model_name(student_id),
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 512, "num_ctx": 2048},
        },
    )
    return resp.json()["response"]


def ask_personal_stream(student_id, context, question):
    import json
    prompt = f"문서:\n{context}\n\n질문: {question}"
    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": personal_model_name(student_id),
            "prompt": prompt,
            "stream": True,
            "options": {"num_predict": 512, "num_ctx": 2048},
        },
        stream=True,
    )
    for line in resp.iter_lines():
        if line:
            token = json.loads(line).get("response", "")
            if token:
                yield token
