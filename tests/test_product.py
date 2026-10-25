import tempfile
import unittest
from pathlib import Path

import app as mockhire_app
from src.product_scoring import star_score, evaluate_product_response


class ProductTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        mockhire_app.app.config.update(TESTING=True, DATABASE=str(Path(self.tmp.name) / "test.db"))
        self.client = mockhire_app.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def test_roles_endpoint(self):
        response = self.client.get('/api/roles')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Data Analyst', response.get_json())

    def test_star_structure_rewards_complete_answer(self):
        strong = 'During a reporting project I needed to reduce delays. I built a Python workflow and reduced turnaround by 30 percent.'
        weak = 'I like working with data.'
        self.assertGreater(star_score(strong), star_score(weak))

    def test_product_evaluation_has_semantic_and_star_dimensions(self):
        result = evaluate_product_response('I built a Python data analysis workflow and improved reporting by 25 percent.', ['python','data','analysis','result'], 'python data analysis result')
        self.assertGreaterEqual(result.star, 0.5)
        self.assertGreaterEqual(result.semantic, 0.0)
        self.assertLessEqual(result.overall, 100)

    def test_end_to_end_interview_persists_history(self):
        roles = self.client.get('/api/roles').get_json()
        role = 'Data Analyst'
        answers = [
            'During a project I needed to analyse customer data. I used SQL and Python, completed the analysis and improved the result by 20 percent.',
            'A stakeholder needed an insight. I analysed the data, explained the impact and the decision improved the outcome by 10 percent.',
            'I validate quality by checking missing values, duplicate rows and source totals before every report.'
        ]
        response = self.client.post('/api/evaluate', json={'candidate':'Test Candidate','role':role,'answers':answers})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(len(payload['evaluations']), len(roles[role]['questions']))
        self.assertEqual(len(payload['history']), 1)
        self.assertGreater(payload['final_score'], 0)

    def test_rejects_incomplete_interview(self):
        response = self.client.post('/api/evaluate', json={'candidate':'Test','role':'Finance Analyst','answers':['only one']})
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
