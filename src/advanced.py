import re
from collections import Counter

from flask import Blueprint, jsonify, request

FILLERS = {'um', 'uh', 'like', 'basically', 'actually', 'literally', 'you know'}


def speech_metrics(transcript: str, duration_seconds=None):
    words = re.findall(r"[A-Za-z']+", transcript.lower())
    filler_count = sum(1 for w in words if w in FILLERS)
    unique_ratio = round(len(set(words)) / max(len(words), 1), 3)
    result = {
        'word_count': len(words),
        'filler_count': filler_count,
        'filler_rate_pct': round(filler_count / max(len(words), 1) * 100, 1),
        'lexical_diversity': unique_ratio,
    }
    if duration_seconds and float(duration_seconds) > 0:
        result['words_per_minute'] = round(len(words) / float(duration_seconds) * 60, 1)
    return result


def adaptive_follow_up(question, answer, score=None, competency='general'):
    text = (answer or '').strip()
    score = float(score) if score is not None else 0
    if len(text.split()) < 35:
        return f'Can you expand on that {competency} example and explain the specific action you personally took?'
    if score and score < 60:
        return 'What measurable result came from your actions, and what would you do differently next time?'
    if not re.search(r'\b(result|outcome|improved|reduced|increased|saved|delivered)\b', text, re.I):
        return 'What was the outcome, and how did you measure whether your approach worked?'
    return f'Good. Now connect that example back to the role: why does it matter for {competency}?'


def register_advanced(app):
    bp = Blueprint('mockhire_advanced', __name__)

    @bp.post('/api/speech/analytics')
    def analyse_speech():
        payload = request.get_json(silent=True) or {}
        transcript = str(payload.get('transcript', '')).strip()
        if not transcript:
            return jsonify({'error': 'transcript is required'}), 400
        return jsonify(speech_metrics(transcript, payload.get('duration_seconds')))

    @bp.post('/api/interview/follow-up')
    def follow_up():
        payload = request.get_json(silent=True) or {}
        if not payload.get('answer'):
            return jsonify({'error': 'answer is required'}), 400
        return jsonify({'follow_up': adaptive_follow_up(payload.get('question', ''), payload['answer'], payload.get('score'), payload.get('competency', 'general'))})

    app.register_blueprint(bp)
