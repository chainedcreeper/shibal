"""학생 상호작용 DB + 학습 트리거 조건."""
import json
import sqlite3

DB_PATH           = "students.db"
TRAIN_THRESHOLD   = 50
RETRAIN_INTERVAL  = 20


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS interactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  TEXT NOT NULL,
            question    TEXT NOT NULL,
            answer      TEXT NOT NULL,
            source      TEXT DEFAULT 'server',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS students (
            student_id         TEXT PRIMARY KEY,
            interaction_count  INTEGER DEFAULT 0,
            model_trained      BOOLEAN DEFAULT FALSE,
            last_trained_at    TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


def log_interaction(student_id, question, answer, source="server"):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO interactions (student_id, question, answer, source) VALUES (?,?,?,?)",
        (student_id, question, answer, source),
    )
    conn.execute(
        """INSERT INTO students (student_id, interaction_count) VALUES (?,1)
           ON CONFLICT(student_id) DO UPDATE SET interaction_count = interaction_count + 1""",
        (student_id,),
    )
    conn.commit()
    conn.close()


def get_student(student_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT interaction_count, model_trained, last_trained_at FROM students WHERE student_id=?",
        (student_id,),
    ).fetchone()
    conn.close()
    if not row:
        return {"interaction_count": 0, "model_trained": False, "last_trained_at": None}
    return {"interaction_count": row[0], "model_trained": bool(row[1]), "last_trained_at": row[2]}


def should_train(student_id):
    s = get_student(student_id)
    count = s["interaction_count"]
    if not s["model_trained"]:
        return count >= TRAIN_THRESHOLD
    conn = sqlite3.connect(DB_PATH)
    new_count = conn.execute(
        "SELECT COUNT(*) FROM interactions WHERE student_id=? "
        "AND created_at > (SELECT last_trained_at FROM students WHERE student_id=?)",
        (student_id, student_id),
    ).fetchone()[0]
    conn.close()
    return new_count >= RETRAIN_INTERVAL


def mark_trained(student_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE students SET model_trained=TRUE, last_trained_at=CURRENT_TIMESTAMP WHERE student_id=?",
        (student_id,),
    )
    conn.commit()
    conn.close()


def export_student_data(student_id, output_path):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT question, answer FROM interactions WHERE student_id=? ORDER BY created_at",
        (student_id,),
    ).fetchall()
    conn.close()
    with open(output_path, "w", encoding="utf-8") as f:
        for q, a in rows:
            f.write(json.dumps({"question": q, "answer": a}, ensure_ascii=False) + "\n")
    return output_path
