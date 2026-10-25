# Security and Responsible Use

## Status

MockHire is a portfolio interview-practice product. It is not an autonomous hiring system and should not be used as the sole basis for employment decisions.

## Current boundary

- Uploaded/interview content should be treated as user-provided personal data.
- The public demo is intended for synthetic or non-sensitive examples.
- Optional semantic models are used for relevance assistance; scoring is not a validated predictor of job performance.
- Protected attributes and biometric/appearance signals are not intended scoring inputs.
- Secrets belong in environment variables; never commit API keys, database credentials or production candidate data.

## Production requirements

A real hiring deployment would require:

- authenticated users and role-based access;
- secure tenant isolation;
- CSRF protection for browser mutations and API authentication for integrations;
- rate limiting and abuse monitoring;
- encrypted transport and secure persistence;
- explicit retention/deletion controls;
- consent and privacy notices;
- accessibility review;
- representative fairness/outcome testing;
- human review and legally validated job-related rubrics;
- audit logging and model/version governance.

## Vulnerability reporting

Please avoid publishing exploitable details or real candidate data in a public issue. Contact the repository owner privately through the GitHub profile with reproduction steps and the affected version.
