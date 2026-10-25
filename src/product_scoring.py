import math
import re
from dataclasses import dataclass
from .evaluator import evaluate_response

STAR_MARKERS = {
    "situation": {"when", "during", "situation", "context", "team", "project"},
    "task": {"needed", "goal", "responsible", "task", "objective", "challenge"},
    "action": {"built", "created", "analysed", "implemented", "led", "designed", "changed", "used"},
    "result": {"result", "improved", "reduced", "increased", "saved", "achieved", "outcome"},
}

@dataclass
class ProductEvaluation:
    relevance: float
    evidence: float
    clarity: float
    star: float
    semantic: float
    overall: float
    feedback: list[str]


def _tokens(text):
    return set(re.findall(r"[a-zA-Z0-9]+", text.lower()))


def lexical_semantic_similarity(answer, reference):
    a, b = _tokens(answer), _tokens(reference)
    if not a or not b:
        return 0.0
    return len(a & b) / math.sqrt(len(a) * len(b))


def semantic_similarity(answer, reference):
    """Use S-BERT when installed; otherwise return a deterministic semantic proxy."""
    try:
        from sentence_transformers import SentenceTransformer
        from sentence_transformers.util import cos_sim
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        vectors = model.encode([answer, reference], convert_to_tensor=True)
        return float(max(0.0, min(1.0, cos_sim(vectors[0], vectors[1]).item())))
    except Exception:
        return lexical_semantic_similarity(answer, reference)


def star_score(answer):
    tokens = _tokens(answer)
    parts = []
    for markers in STAR_MARKERS.values():
        parts.append(1.0 if tokens & markers else 0.0)
    # Numbers are useful evidence of results.
    if re.search(r"\b\d+(?:\.\d+)?%?\b", answer):
        parts[-1] = 1.0
    return round(sum(parts) / 4.0, 3)


def evaluate_product_response(answer, keywords, reference_text=""):
    base = evaluate_response(answer, keywords)
    reference = reference_text or " ".join(keywords)
    semantic = round(semantic_similarity(answer, reference), 3)
    star = star_score(answer)
    overall = round(
        (0.30 * base.relevance + 0.20 * base.evidence + 0.10 * base.clarity + 0.20 * star + 0.20 * semantic) * 100,
        1,
    )
    feedback = list(base.feedback)
    if star < 0.75:
        feedback.append("Use a clearer STAR structure: situation, task, action and measurable result.")
    if semantic < 0.35:
        feedback.append("Connect the answer more directly to the competency being assessed.")
    return ProductEvaluation(base.relevance, base.evidence, base.clarity, star, semantic, overall, feedback)
