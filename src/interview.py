from dataclasses import dataclass
from .evaluator import Evaluation, evaluate_response

@dataclass
class Question:
    text: str
    competency: str
    keywords: list[str]
    weight: float = 1.0


def score_interview(questions: list[Question], answers: list[str]) -> dict:
    if len(questions) != len(answers):
        raise ValueError("questions and answers must have the same length")
    evaluations: list[Evaluation] = []
    weighted = 0.0
    total_weight = 0.0
    for question, answer in zip(questions, answers):
        result = evaluate_response(answer, question.keywords)
        evaluations.append(result)
        weighted += result.overall * question.weight
        total_weight += question.weight
    final_score = round(weighted / total_weight, 1) if total_weight else 0.0
    return {"final_score": final_score, "evaluations": evaluations}
