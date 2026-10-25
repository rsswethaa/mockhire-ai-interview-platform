import re
from dataclasses import dataclass

ACTION_WORDS = {"built", "led", "improved", "reduced", "increased", "designed", "implemented", "analysed", "managed"}

@dataclass
class Evaluation:
    relevance: float
    evidence: float
    clarity: float
    overall: float
    feedback: list[str]


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def evaluate_response(answer: str, keywords: list[str]) -> Evaluation:
    tokens = _tokens(answer)
    token_set = set(tokens)
    expected = {k.lower() for k in keywords}
    relevance = 0.0 if not expected else len(token_set & expected) / len(expected)
    evidence_hits = sum(1 for t in tokens if t in ACTION_WORDS or re.fullmatch(r"\d+", t))
    evidence = min(1.0, evidence_hits / 3)
    length = len(tokens)
    clarity = 1.0 if 25 <= length <= 180 else max(0.2, 1 - abs(length - 80) / 160)
    overall = round((0.5 * relevance + 0.3 * evidence + 0.2 * clarity) * 100, 1)
    feedback = []
    if relevance < 0.5:
        feedback.append("Address more of the role-specific concepts in the question.")
    if evidence < 0.5:
        feedback.append("Add a concrete action, result or measurable outcome.")
    if clarity < 0.6:
        feedback.append("Make the answer more concise and structured.")
    if not feedback:
        feedback.append("Strong structure: relevant, evidence-based and clear.")
    return Evaluation(round(relevance, 3), round(evidence, 3), round(clarity, 3), overall, feedback)
