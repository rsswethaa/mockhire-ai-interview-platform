# Architecture

```mermaid
sequenceDiagram
  participant C as Candidate
  participant I as Interview Engine
  participant E as Evaluator
  participant R as Report
  C->>I: Answer question
  I->>E: Answer + competency keywords
  E->>E: relevance/evidence/clarity signals
  E-->>I: explainable score
  I-->>R: weighted scorecard
```

The reference implementation uses transparent lexical/evidence signals so tests are deterministic. A production research version could replace or augment relevance scoring with sentence embeddings or an LLM while retaining auditability and human review.
