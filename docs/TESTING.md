# Testing Strategy

## Automated coverage
- relevant evidence-rich answers score above unrelated answers
- weighted interview aggregation behaves correctly
- mismatched question/answer counts are rejected
- SQLite schema and seed data initialise cleanly
- interview sessions, responses and evaluations persist correctly
- empty responses are rejected

Run:
```bash
python -m unittest discover -s tests -v
```

GitHub Actions also compiles source/test modules and executes the test suite on pushes and pull requests.

## Future validation
A research-grade hiring system would additionally require rubric agreement studies, subgroup fairness tests, accessibility testing, calibration, inter-rater comparison and adversarial prompt/response tests.
