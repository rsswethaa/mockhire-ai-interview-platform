# Production hardening

MockHire supports local SQLite-backed platform metadata for development and a managed PostgreSQL database through `DATABASE_URL` in production. The platform layer provides user registration/login, admin/user roles, API-key issuance, per-route rate limiting, structured JSON request logs, Prometheus-style counters, optional Sentry integration, model/version registration, experiment tracking and CSV audit export.

## Environment variables
- `DATABASE_URL` - PostgreSQL connection string on Render; SQLite fallback is used locally.
- `SECRET_KEY` - signing key for login tokens.
- `SENTRY_DSN` - optional error tracking.
- `RATE_LIMIT_PER_MINUTE` - defaults to 120.

## Release process
`VERSION` tracks semantic versioning. Pushing a tag such as `v1.0.0` triggers `.github/workflows/release.yml` to create a GitHub Release automatically.

## Demo integrity
The public demo can remain open for interview practice while admin/model/experiment endpoints require a signed user token or issued API key. Speech analytics are transcript-based and do not claim clinical or psychometric validity.
