"""학생 노트 저장 — 채팅/분석 답변에서 📌 저장 → 모아보기."""
import sqlite3

DB_PATH = "students.db"


def init_notes_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  TEXT NOT NULL,
            category    TEXT DEFAULT 'general',  -- general / exam / important
            content     TEXT NOT NULL,
            source      TEXT DEFAULT 'manual',   -- chat / analyze / manual
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def add_note(student_id: str, content: str, category: str = "general", source: str = "manual") -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "INSERT INTO notes (student_id, category, content, source) VALUES (?, ?, ?, ?)",
        (student_id, category, content, source),
    )
    note_id = cur.lastrowid
    conn.commit()
    conn.close()
    return note_id


def list_notes(student_id: str, category: str | None = None) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    if category:
        rows = conn.execute(
            "SELECT id, category, content, source, created_at "
            "FROM notes WHERE student_id=? AND category=? ORDER BY created_at DESC",
            (student_id, category),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, category, content, source, created_at "
            "FROM notes WHERE student_id=? ORDER BY created_at DESC",
            (student_id,),
        ).fetchall()
    conn.close()
    return [
        {"id": r[0], "category": r[1], "content": r[2], "source": r[3], "created_at": r[4]}
        for r in rows
    ]


def delete_note(student_id: str, note_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "DELETE FROM notes WHERE id=? AND student_id=?",
        (note_id, student_id),
    )
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def update_note_category(student_id: str, note_id: int, category: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "UPDATE notes SET category=? WHERE id=? AND student_id=?",
        (category, note_id, student_id),
    )
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0
