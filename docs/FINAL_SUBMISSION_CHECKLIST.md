# Final Submission Checklist

## Code and Build

- Backend tests pass: python -m pytest backend/tests -q
- Frontend lint/build pass: cd frontend && npm run lint && npm run build
- Security suite pass: scripts/run_security_test
- Resilience suite pass: scripts/run_resilience_test
- Cookie-session smoke pass: scripts/run_cookie_smoke_test
- Notification chain pass: scripts/run_notification_chain_test

## Operations

- Production compose verified: scripts/verify_prod_stack
- Clean deploy simulation verified: scripts/simulate_clean_deploy
- Backup script tested: scripts/backup_db.sh or scripts/backup_db.ps1

## Documentation

- README updated with setup, architecture, and contribution section
- API reference updated
- NDMC deployment runbook updated
- UAT plan and user manual finalized
- Presentation outline finalized
- Screenshot checklist completed

## Release

- Code freeze checklist complete
- Local release tag created: v1.0-rc1
- CI workflows green on main branch
- Release notes/changelog prepared

## Final Package

- Source code archive
- Project report PDF
- Presentation PPT/PDF
- Screenshots pack
- Deployment and operations docs
