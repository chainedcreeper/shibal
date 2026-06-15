"""학생 학습 일정 — 날짜별 할 일 목록."""
import sqlite3

DB_PATH = "students.db"


def init_schedule_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  TEXT NOT NULL,
            date        TEXT NOT NULL,        -- YYYY-MM-DD
            title       TEXT NOT NULL,
            note        TEXT DEFAULT '',
            done        INTEGER DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def add_schedule(student_id: str, date: str, title: str, note: str = "") -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "INSERT INTO schedules (student_id, date, title, note) VALUES (?, ?, ?, ?)",
        (student_id, date, title, note),
    )
    sched_id = cur.lastrowid
    conn.commit()
    conn.close()
    return sched_id


def list_schedules(student_id: str) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, date, title, note, done FROM schedules "
        "WHERE student_id=? ORDER BY date ASC, id ASC",
        (student_id,),
    ).fetchall()
    conn.close()
    return [
        {"id": r[0], "date": r[1], "title": r[2], "note": r[3], "done": bool(r[4])}
        for r in rows
    ]


def update_schedule(student_id: str, sched_id: int, **kwargs) -> bool:
    fields = []
    values = []
    for k in ("date", "title", "note", "done"):
        if k in kwargs and kwargs[k] is not None:
            fields.append(f"{k}=?")
            values.append(int(kwargs[k]) if k == "done" else kwargs[k])
    if not fields:
        return False
    values.extend([sched_id, student_id])
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        f"UPDATE schedules SET {', '.join(fields)} WHERE id=? AND student_id=?",
        values,
    )
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def delete_schedule(student_id: str, sched_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "DELETE FROM schedules WHERE id=? AND student_id=?",
        (sched_id, student_id),
    )
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0
