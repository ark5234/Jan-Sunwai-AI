# Code Freeze Policy (May 02, 2026)

This repository is now in code-freeze mode for release readiness.

## Freeze Scope

- Backend dependencies pinned in backend/requirements.txt.
- Frontend dependencies pinned in frontend/package.json with package-lock.json as lock source.
- New packages are blocked unless explicitly approved and documented.

## Allowed During Freeze

- Bug fixes.
- Documentation updates.
- Test reliability fixes.
- Release automation updates.

## Blocked During Freeze

- New product features.
- Schema-breaking API changes.
- Unreviewed dependency additions or upgrades.

## Change Control

1. Open an issue tagged freeze-exception.
2. Document risk, rollback plan, and test evidence.
3. Require explicit maintainer approval before merge.

## Verification Commands

- Backend: python -m pytest backend/tests -q
- Frontend: cd frontend && npm run lint && npm run build
- Security: scripts/run_security_test.bat (Windows) or bash scripts/run_security_test.sh
- Resilience: scripts/run_resilience_test.bat (Windows) or bash scripts/run_resilience_test.sh
