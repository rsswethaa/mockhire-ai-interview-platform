import json
from pathlib import Path

from .storage import connect, init_db, record_response, save_evaluation, complete_session


def ensure_ready(db_path):
    path = Path(db_path)
    if not path.exists():
        init_db(path, seed=False)
    return path


def sync_catalog(db_path, roles):
    ensure_ready(db_path)
    question_ids = {}
    with connect(db_path) as db:
        for title, config in roles.items():
            db.execute("INSERT OR IGNORE INTO roles(title, description) VALUES (?,?)", (title, config.get("description", "")))
            role_id = db.execute("SELECT id FROM roles WHERE title=?", (title,)).fetchone()["id"]
            for item in config["questions"]:
                row = db.execute(
                    "SELECT id FROM questions WHERE role_id=? AND question_text=?",
                    (role_id, item["question"]),
                ).fetchone()
                if row is None:
                    cur = db.execute(
                        "INSERT INTO questions(role_id, competency, question_text, weight) VALUES (?,?,?,?)",
                        (role_id, item["competency"], item["question"], item.get("weight", 1.0)),
                    )
                    qid = cur.lastrowid
                else:
                    qid = row["id"]
                question_ids[(title, item["question"])] = qid
    return question_ids


def ensure_candidate(db_path, external_ref, display_name=None):
    ensure_ready(db_path)
    with connect(db_path) as db:
        db.execute(
            "INSERT OR IGNORE INTO candidates(external_ref, display_name) VALUES (?,?)",
            (external_ref, display_name or external_ref),
        )
        if display_name:
            db.execute("UPDATE candidates SET display_name=? WHERE external_ref=?", (display_name, external_ref))
        return db.execute("SELECT id FROM candidates WHERE external_ref=?", (external_ref,)).fetchone()["id"]


def create_product_session(db_path, external_ref, display_name, role_title):
    candidate_id = ensure_candidate(db_path, external_ref, display_name)
    with connect(db_path) as db:
        role = db.execute("SELECT id FROM roles WHERE title=?", (role_title,)).fetchone()
        if role is None:
            raise ValueError("role does not exist")
        cur = db.execute(
            "INSERT INTO interview_sessions(candidate_id, role_id) VALUES (?,?)",
            (candidate_id, role["id"]),
        )
        return cur.lastrowid


def persist_evaluation(db_path, session_id, question_id, answer, evaluation):
    response_id = record_response(db_path, session_id, question_id, answer)
    save_evaluation(db_path, response_id, evaluation, model_version="hybrid-semantic-star-v2")
    return response_id


def candidate_history(db_path, external_ref, limit=10):
    ensure_ready(db_path)
    with connect(db_path) as db:
        rows = db.execute(
            """
            SELECT s.id, r.title AS role, s.final_score, s.status, s.created_at
            FROM interview_sessions s
            JOIN candidates c ON c.id=s.candidate_id
            JOIN roles r ON r.id=s.role_id
            WHERE c.external_ref=? AND s.status='COMPLETED'
            ORDER BY s.id DESC LIMIT ?
            """,
            (external_ref, int(limit)),
        ).fetchall()
        return [dict(row) for row in rows]


def competency_summary(db_path, external_ref):
    ensure_ready(db_path)
    with connect(db_path) as db:
        rows = db.execute(
            """
            SELECT q.competency, ROUND(AVG(e.overall),1) AS average_score, COUNT(*) AS attempts
            FROM evaluations e
            JOIN responses p ON p.id=e.response_id
            JOIN questions q ON q.id=p.question_id
            JOIN interview_sessions s ON s.id=p.session_id
            JOIN candidates c ON c.id=s.candidate_id
            WHERE c.external_ref=?
            GROUP BY q.competency ORDER BY average_score DESC
            """,
            (external_ref,),
        ).fetchall()
        return [dict(row) for row in rows]
