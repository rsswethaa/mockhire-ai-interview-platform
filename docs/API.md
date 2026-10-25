# Interface Contracts

This repository exposes Python service interfaces rather than a public HTTP API.

## Evaluation
`evaluate_response(answer: str, keywords: list[str]) -> Evaluation`

Returns relevance, evidence, clarity, overall score and explainable feedback.

## Interview orchestration
`score_interview(questions, answers) -> dict`

Returns a weighted final score and individual evaluations.

## Persistence
- `init_db(path, seed=False)`
- `create_session(path, external_ref, role_title)`
- `record_response(path, session_id, question_id, answer_text)`
- `save_evaluation(path, response_id, evaluation, model_version)`
- `complete_session(path, session_id, final_score)`

A production API could wrap these functions with authenticated REST/GraphQL endpoints while preserving the same validation and audit model.
