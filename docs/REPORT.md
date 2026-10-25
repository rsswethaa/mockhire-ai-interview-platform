# Technical Project Report — MockHire AI Interview Platform

## Executive summary
MockHire demonstrates an end-to-end structured interview workflow: role setup, question planning, candidate sessions, response evaluation, persistence, audit history and human-review outputs.

## 1. Problem
Interview assessment can become inconsistent when questions, competencies and evidence standards vary between interviewers.

## 2. Objectives
Create a reproducible interview engine; connect questions to competencies; score answers transparently; persist an audit trail; and keep a human reviewer in control.

## 3. Functional design
The system models roles, candidates, questions, interview sessions, responses and evaluations. The evaluator produces component scores for relevance, evidence and clarity, then the interview engine aggregates weighted scores.

## 4. Data design
SQLite stores the interview workflow and the evaluator version used for each scored response. This makes later inspection possible and separates transient computation from durable records.

## 5. Architecture
The code is split into evaluation (`src/evaluator.py`), interview orchestration (`src/interview.py`) and persistence (`src/storage.py`). SQL definitions are version-controlled under `database/`.

## 6. Testing
Unit tests cover scoring behaviour and invalid input. Storage tests create an isolated temporary database and validate the complete candidate-session-response-evaluation flow. CI compiles and executes all tests.

## 7. Responsible AI
No autonomous hiring decision should rely on this prototype. Real deployment requires job-related validation, candidate notice, fairness and accessibility testing, privacy governance, human review and legal compliance.

## 8. Limitations
The baseline relies on transparent lexical heuristics, not validated semantic assessment. No predictive validity, fairness, hiring-outcome accuracy or legal compliance claim is made.

## 9. Future work
Sentence embeddings, calibrated rubrics, interviewer notes, role libraries, bias audits, candidate-consent workflows, model/version registries and human-in-the-loop review tooling.

## Conclusion
The repository is structured as a complete software project rather than a README-only concept: executable logic, persistence, database assets, diagrams, tests, CI, operational docs and a formal report are all included.
