import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.evaluator import evaluate_response
from src.storage import complete_session, create_session, init_db, record_response, save_evaluation


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / 'mockhire.db'
        init_db(self.db, seed=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_seed_and_audit_flow(self):
        session_id = create_session(self.db, 'DEMO-001', 'Business Analyst')
        with sqlite3.connect(self.db) as db:
            question_id = db.execute('SELECT id FROM questions ORDER BY id LIMIT 1').fetchone()[0]
        response_id = record_response(self.db, session_id, question_id, 'I built a Python data analysis workflow and improved result 20 percent.')
        result = evaluate_response('I built a Python data analysis workflow and improved result 20 percent.', ['python','data','analysis','result'])
        save_evaluation(self.db, response_id, result)
        complete_session(self.db, session_id, result.overall)
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM evaluations').fetchone()[0], 1)
            row = db.execute('SELECT status, final_score FROM interview_sessions WHERE id=?', (session_id,)).fetchone()
        self.assertEqual(row[0], 'COMPLETED')
        self.assertGreater(row[1], 0)

    def test_empty_response_rejected(self):
        session_id = create_session(self.db, 'DEMO-001', 'Business Analyst')
        with sqlite3.connect(self.db) as db:
            question_id = db.execute('SELECT id FROM questions LIMIT 1').fetchone()[0]
        with self.assertRaises(ValueError):
            record_response(self.db, session_id, question_id, '   ')


if __name__ == '__main__':
    unittest.main()
