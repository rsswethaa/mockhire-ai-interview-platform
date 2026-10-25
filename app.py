import hashlib
import json
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from src.product_scoring import evaluate_product_response
from src.product_storage import candidate_history, competency_summary, complete_session, create_product_session, persist_evaluation, sync_catalog

ROOT = Path(__file__).resolve().parent
ROLES_PATH = ROOT / "data" / "roles.json"

app = Flask(__name__)
app.config["DATABASE"] = os.getenv("MOCKHIRE_DB", str(ROOT / "mockhire.db"))


def load_roles():
    return json.loads(ROLES_PATH.read_text(encoding="utf-8"))


def candidate_ref(name):
    cleaned = (name or "demo-candidate").strip().lower().encode("utf-8")
    return hashlib.sha256(cleaned).hexdigest()[:16]


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/roles")
def api_roles():
    roles = load_roles()
    sync_catalog(app.config["DATABASE"], roles)
    return jsonify(roles)


@app.post("/api/evaluate")
def api_evaluate():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("candidate") or "Demo Candidate").strip()
    role_title = payload.get("role")
    answers = payload.get("answers") or []
    roles = load_roles()
    if role_title not in roles:
        return jsonify({"error": "Unknown role"}), 400
    questions = roles[role_title]["questions"]
    if len(answers) != len(questions) or any(not str(a).strip() for a in answers):
        return jsonify({"error": "Answer every interview question"}), 400
    db_path = app.config["DATABASE"]
    question_ids = sync_catalog(db_path, roles)
    ref = candidate_ref(name)
    session_id = create_product_session(db_path, ref, name, role_title)
    items = []
    weighted = 0.0
    total_weight = 0.0
    for question, answer in zip(questions, answers):
        reference = f"{question['question']} {' '.join(question['keywords'])}"
        result = evaluate_product_response(str(answer), question["keywords"], reference)
        qid = question_ids[(role_title, question["question"])]
        persist_evaluation(db_path, session_id, qid, str(answer), result)
        weight = float(question.get("weight", 1.0))
        weighted += result.overall * weight
        total_weight += weight
        items.append({"question": question["question"], "competency": question["competency"], "overall": result.overall, "relevance": round(result.relevance * 100, 1), "evidence": round(result.evidence * 100, 1), "clarity": round(result.clarity * 100, 1), "star": round(result.star * 100, 1), "semantic": round(result.semantic * 100, 1), "feedback": result.feedback})
    final_score = round(weighted / total_weight, 1) if total_weight else 0.0
    complete_session(db_path, session_id, final_score)
    return jsonify({"session_id": session_id, "candidate": name, "role": role_title, "final_score": final_score, "evaluations": items, "history": candidate_history(db_path, ref), "competencies": competency_summary(db_path, ref)})


@app.get("/api/history")
def api_history():
    name = request.args.get("candidate", "Demo Candidate")
    ref = candidate_ref(name)
    return jsonify({"history": candidate_history(app.config["DATABASE"], ref), "competencies": competency_summary(app.config["DATABASE"], ref)})


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "mockhire"})


from src.advanced import register_advanced
from src.platform import init_platform
register_advanced(app)
init_platform(app, 'mockhire')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv('FLASK_DEBUG') == '1')
