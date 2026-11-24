# Contributing

## Engineering principles
- Preserve original evidence and provenance; do not silently rewrite source records.
- Keep facts, correlations, inferences and unknowns distinct.
- Enforce tenant scope on every resource query and mutation.
- Do not collect chain-of-thought, secrets or unnecessary sensitive content.
- Do not claim a connector is live unless it has authentication, retry, checkpoint, backfill and integration tests.
- Keep cloud and customer-controlled deployment paths aligned.

## Before opening a pull request
Run:

```bash
pip install -e "./apps/api[dev]"
pytest -q apps/api/tests
ruff check apps/api/src apps/api/tests
pip install -e "./packages/python-sdk[dev]"
pytest -q packages/python-sdk/tests
cd apps/web && npm install && npm run build
cd ../../packages/typescript-sdk && npm install && npm run build
```

## Required tests
Include tests for success, invalid input, idempotent replay, cross-tenant access, role denial and relevant failure modes. Evidence and connector changes must test provenance, redaction and digest/custody behavior.
