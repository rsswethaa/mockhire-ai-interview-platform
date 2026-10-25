# Technical Report

## Problem
Interview assessment can be inconsistent when questions, competencies and evidence standards vary between interviewers.

## Objective
Demonstrate an intelligent interview workflow that links questions to competencies and generates a structured, explainable scorecard.

## Method
The prototype extracts role-keyword coverage, evidence/action signals and answer-length clarity. Weighted question scores are aggregated into an interview score.

## Evaluation
Unit tests validate that relevant evidence-rich answers score above unrelated answers, that weighting behaves correctly and that invalid session data is rejected.

## Responsible-use boundary
The system is not intended to make autonomous employment decisions. Real hiring systems require validated job-related criteria, bias testing, accessibility controls, privacy governance, human review and compliance with applicable employment law.

## Future work
Semantic embeddings, calibrated rubrics, interviewer notes, role libraries, candidate consent, bias audits and human-in-the-loop review.
