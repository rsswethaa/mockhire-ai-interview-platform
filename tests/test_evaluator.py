import unittest
from src.evaluator import evaluate_response
from src.interview import Question, score_interview

class EvaluatorTests(unittest.TestCase):
    def test_relevant_answer_scores_higher(self):
        strong = evaluate_response("I built a Python data analysis and improved result 25", ["python", "data", "analysis", "result"])
        weak = evaluate_response("I enjoy learning new things", ["python", "data", "analysis", "result"])
        self.assertGreater(strong.overall, weak.overall)

    def test_interview_weighting(self):
        qs = [Question("q1", "x", ["python"], 2), Question("q2", "y", ["stakeholder"], 1)]
        result = score_interview(qs, ["I built python tool 20", "stakeholder communication"])
        self.assertGreater(result["final_score"], 0)

    def test_mismatched_inputs(self):
        with self.assertRaises(ValueError):
            score_interview([Question("q", "x", [])], [])

if __name__ == "__main__":
    unittest.main()
