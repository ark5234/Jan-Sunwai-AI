# Contributing Guide

## Branching

- Branch from main using feature/<scope> or fix/<scope>.
- Keep PRs focused and small.

## Local Setup

1. Backend dependencies:
   - python -m pip install -r backend/requirements.txt
2. Frontend dependencies:
   - cd frontend && npm install
3. Environment:
   - configure backend/.env

## Quality Gates

- Backend tests: python -m pytest backend/tests -q
- Frontend checks: cd frontend && npm run lint && npm run build
- Security checks: scripts/run_security_test
- Resilience checks: scripts/run_resilience_test

## Commit Guidelines

- Use clear, imperative messages.
- Include why and impact in PR description.
- Link related issue/timeline item.

## Release Process

- Run full checks.
- Execute scripts/release_rc1 to create local release tag.
- Push tag after maintainer approval.
