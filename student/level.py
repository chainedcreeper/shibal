"""학생 이해도 수준 평가.

흐름:
  1. LLM 이 질문 보고 1~10 점수 부여 (자동 라벨링)
  2. 50개 누적되면 sklearn RandomForest 분류기 학습
  3. 분류기 학습 후엔 LLM 없이 빠른 추론
"""
import os
import pickle
import re
import sqlite3

import requests
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

from rag.embedding import model as embed_model

DB_PATH                   = "students.db"
MODEL_DIR                 = "level_models"
CLASSIFIER_TRAIN_THRESHOLD = 50
DECAY                     = 0.92

LEVEL_LABELS = {
    (1, 3):  "입문",
    (4, 6):  "중급",
    (7, 10): "심화",
}


def init_level_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS level_scores (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  TEXT NOT NULL,
            question    TEXT NOT NULL,
            score       REAL NOT NULL,
            method      TEXT DEFAULT 'llm',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS student_levels (
            student_id       TEXT PRIMARY KEY,
            current_level    REAL DEFAULT 5.0,
            label            TEXT DEFAULT '중급',
            score_count      INTEGER DEFAULT 0,
            classifier_ready BOOLEAN DEFAULT FALSE
        )
    """)
    conn.commit()
    conn.close()


# ── LLM 점수 ──────────────────────────────────────────
def _llm_score(question: str) -> float:
    prompt = f"""학생이 다음 질문을 했다. 이 질문이 얼마나 깊은 이해를 반영하는지 1~10점으로만 답하라.

기준:
1~3  = 개념 정의 질문 ("~이 뭐야?", "~가 뭔가요?")
4~6  = 원리/이유 질문 ("왜 ~?", "어떻게 ~?")
7~10 = 분석/비교/응용 질문 ("~와 ~의 차이", "~가 ~에 미치는 영향")

질문: {question}

숫자만 출력 (예: 7)"""

    try:
        resp = requests.post(
            f"{os.getenv('OLLAMA_HOST', 'http://localhost:11434')}/api/generate",
            json={
                "model": os.getenv("OLLAMA_MODEL", "qwen3:8b"),
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 5, "num_ctx": 512},
            },
            timeout=30,
        )
        raw = resp.json()["response"].strip()
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        score = float(re.search(r"\d+(\.\d+)?", raw).group())
        return max(1.0, min(10.0, score))
    except Exception:
        return 5.0


# ── 분류기 ────────────────────────────────────────────
def _classifier_path(student_id: str) -> str:
    return os.path.join(MODEL_DIR, f"{student_id}_clf.pkl")


def _classifier_exists(student_id: str) -> bool:
    return os.path.exists(_classifier_path(student_id))


def _clf_score(student_id: str, question: str) -> float:
    with open(_classifier_path(student_id), "rb") as f:
        clf, le = pickle.load(f)
    emb     = embed_model.encode([question])
    label   = le.inverse_transform(clf.predict(emb))[0]
    mapping = {"입문": 2.0, "중급": 5.0, "심화": 8.5}
    return mapping.get(label, 5.0)


def train_classifier(student_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT question, score FROM level_scores WHERE student_id=? ORDER BY created_at",
        (student_id,),
    ).fetchall()
    conn.close()

    if len(rows) < CLASSIFIER_TRAIN_THRESHOLD:
        return False

    questions, scores = zip(*rows)
    labels = []
    for s in scores:
        if   s <= 3: labels.append("입문")
        elif s <= 6: labels.append("중급")
        else:        labels.append("심화")

    embeddings = embed_model.encode(list(questions))
    le         = LabelEncoder()
    y          = le.fit_transform(labels)

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(embeddings, y)

    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(_classifier_path(student_id), "wb") as f:
        pickle.dump((clf, le), f)

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE student_levels SET classifier_ready=TRUE WHERE student_id=?",
        (student_id,),
    )
    conn.commit()
    conn.close()
    return True


# ── 수준 업데이트 ─────────────────────────────────────
def _weighted_average(scores: list[float]) -> float:
    if not scores:
        return 5.0
    weights = [DECAY ** i for i in range(len(scores) - 1, -1, -1)]
    return sum(s * w for s, w in zip(scores, weights)) / sum(weights)


def _score_to_label(score: float) -> str:
    for (lo, hi), label in LEVEL_LABELS.items():
        if lo <= round(score) <= hi:
            return label
    return "중급"


def assess_and_update(student_id: str, question: str) -> dict:
    if _classifier_exists(student_id):
        score, method = _clf_score(student_id, question), "classifier"
    else:
        score, method = _llm_score(question), "llm"

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO level_scores (student_id, question, score, method) VALUES (?,?,?,?)",
        (student_id, question, score, method),
    )

    rows = conn.execute(
        "SELECT score FROM level_scores WHERE student_id=? ORDER BY created_at DESC LIMIT 20",
        (student_id,),
    ).fetchall()
    current_level = _weighted_average([r[0] for r in rows])
    label         = _score_to_label(current_level)

    conn.execute("""
        INSERT INTO student_levels (student_id, current_level, label, score_count)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(student_id) DO UPDATE SET
            current_level = ?,
            label = ?,
            score_count = score_count + 1
    """, (student_id, current_level, label, current_level, label))
    conn.commit()

    count = conn.execute(
        "SELECT score_count FROM student_levels WHERE student_id=?", (student_id,)
    ).fetchone()[0]
    conn.close()

    if count >= CLASSIFIER_TRAIN_THRESHOLD and not _classifier_exists(student_id):
        train_classifier(student_id)

    return {
        "score":  round(score, 1),
        "level":  round(current_level, 1),
        "label":  label,
        "method": method,
    }


def get_student_level(student_id: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT current_level, label, score_count, classifier_ready FROM student_levels WHERE student_id=?",
        (student_id,),
    ).fetchone()
    conn.close()
    if not row:
        return {"level": 5.0, "label": "중급", "score_count": 0, "classifier_ready": False}
    return {
        "level":            row[0],
        "label":            row[1],
        "score_count":      row[2],
        "classifier_ready": bool(row[3]),
    }
