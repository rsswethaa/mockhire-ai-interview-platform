from pathlib import Path
import json
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / 'database' / 'schema.sql'
SEED = ROOT / 'database' / 'seed.sql'


def connect(db_path):
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    return db


def init_db(db_path, seed=False):
    with connect(db_path) as db:
        db.executescript(SCHEMA.read_text(encoding='utf-8'))
        if seed:
            db.executescript(SEED.read_text(encoding='utf-8'))
    return Path(db_path)


def create_session(db_path, external_ref, role_title):
    with connect(db_path) as db:
        candidate = db.execute('SELECT id FROM candidates WHERE external_ref=?', (external_ref,)).fetchone()
        role = db.execute('SELECT id FROM roles WHERE title=?', (role_title,)).fetchone()
        if not candidate or not role:
            raise ValueError('candidate and role must exist')
        cur = db.execute('INSERT INTO interview_sessions(candidate_id, role_id) VALUES (?,?)', (candidate['id'], role['id']))
        return cur.lastrowid


def record_response(db_path, session_id, question_id, answer_text):
    if not answer_text.strip():
        raise ValueError('answer_text is required')
    with connect(db_path) as db:
        cur = db.execute('INSERT INTO responses(session_id, question_id, answer_text) VALUES (?,?,?)', (session_id, question_id, answer_text.strip()))
        return cur.lastrowid


def save_evaluation(db_path, response_id, evaluation, model_version='rule-baseline-v1'):
    with connect(db_path) as db:
        db.execute('''INSERT INTO evaluations(response_id,relevance,evidence,clarity,overall,feedback_json,model_version)
                      VALUES (?,?,?,?,?,?,?)''',
                   (response_id, evaluation.relevance, evaluation.evidence, evaluation.clarity,
                    evaluation.overall, json.dumps(evaluation.feedback), model_version))


def complete_session(db_path, session_id, final_score):
    with connect(db_path) as db:
        db.execute("UPDATE interview_sessions SET status='COMPLETED', final_score=?, completed_at=CURRENT_TIMESTAMP WHERE id=?",
                   (float(final_score), session_id))
