-- Session summary
SELECT s.id, c.display_name, r.title, s.status, s.final_score, s.created_at
FROM interview_sessions s
JOIN candidates c ON c.id=s.candidate_id
JOIN roles r ON r.id=s.role_id
ORDER BY s.id DESC;

-- Detailed response/evaluation audit trail
SELECT s.id AS session_id, q.competency, q.question_text, p.answer_text,
       e.relevance, e.evidence, e.clarity, e.overall, e.model_version
FROM responses p
JOIN interview_sessions s ON s.id=p.session_id
JOIN questions q ON q.id=p.question_id
LEFT JOIN evaluations e ON e.response_id=p.id
ORDER BY s.id, p.id;

-- Average score by competency
SELECT q.competency, ROUND(AVG(e.overall),1) AS avg_score
FROM evaluations e
JOIN responses p ON p.id=e.response_id
JOIN questions q ON q.id=p.question_id
GROUP BY q.competency;
