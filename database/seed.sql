INSERT OR IGNORE INTO roles(title, description) VALUES
('Business Analyst','Analytical problem solving, stakeholder communication and delivery planning.');

INSERT OR IGNORE INTO candidates(external_ref, display_name) VALUES
('DEMO-001','Demo Candidate');

INSERT INTO questions(role_id, competency, question_text, weight)
SELECT id, 'data_analysis', 'Describe a data problem you solved.', 1.2 FROM roles WHERE title='Business Analyst'
AND NOT EXISTS (SELECT 1 FROM questions WHERE question_text='Describe a data problem you solved.');

INSERT INTO questions(role_id, competency, question_text, weight)
SELECT id, 'communication', 'Explain a time you influenced a stakeholder.', 1.0 FROM roles WHERE title='Business Analyst'
AND NOT EXISTS (SELECT 1 FROM questions WHERE question_text='Explain a time you influenced a stakeholder.');
