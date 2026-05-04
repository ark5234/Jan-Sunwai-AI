# UAT Plan

This plan completes the UAT setup, citizen/admin execution scripts, and feedback loop process.

## 1. UAT Setup (May 11)

## Environment

- Backend URL: http://localhost:8000
- Frontend URL: http://localhost:5173
- Database: clean staging copy of jan_sunwai_db
- Models loaded: qwen2.5vl:3b, granite3.2-vision:2b, llama3.2:1b

## Seed Accounts

- Citizen: citizen_demo / citizen123
- Dept Head: department-specific account from hierarchy (example: health_moh / health123)
- Admin: admin_demo / admin123
- Worker pool seeded using backend/create_test_users.py

## Pre-flight

1. Run scripts/simulate_clean_deploy.bat (Windows) or bash scripts/simulate_clean_deploy.sh.
2. Run scripts/run_tests.bat (Windows) or bash scripts/run_tests.sh.
3. Run scripts/run_cookie_smoke_test.bat (Windows) or bash scripts/run_cookie_smoke_test.sh.
4. Run scripts/run_notification_chain_test.bat (Windows) or bash scripts/run_notification_chain_test.sh.

For notification-chain script on local demo data, set env vars before running:

- `API_BASE_URL=http://localhost:8000/api/v1`
- `CITIZEN_USERNAME=citizen_demo`
- `CITIZEN_PASSWORD=citizen123`
- `DEPT_HEAD_USERNAME=admin_demo`
- `DEPT_HEAD_PASSWORD=admin123`

## 2. Citizen Persona Script (May 12)

1. Login as citizen.
2. Open Analyze page.
3. Upload image and verify compression summary.
4. Verify generated draft and map location.
5. Adjust marker manually if needed.
6. Submit complaint.
7. Check complaint appears in citizen dashboard with status Open/In Progress.
8. Verify unread notification count updates after dept-head status change.

Pass criteria:

- No blocking error in upload/api/v1/analyze/submit flow.
- Complaint ID generated and visible.
- Status and timeline render correctly.

## 3. Admin Persona Script (May 13)

1. Login as admin.
2. Open admin dashboard and verify complaint listing.
3. Filter by department/status.
4. Perform bulk status update.
5. Open heatmap tab and verify data render.
6. Reassign worker from assignment controls.
7. Export CSV and validate columns.

Pass criteria:

- Admin actions apply successfully with correct role restrictions.
- Analytics and heatmap data load without UI breakage.

## 4. Feedback Loop (May 14)

## Collection Template

- Persona:
- Step:
- Observed friction:
- Severity: low | medium | high
- Suggested fix:
- Applied fix commit/PR:

## Prioritization Rule

- High: breakage or data-loss risk. Fix immediately.
- Medium: slows critical flow. Fix in same sprint.
- Low: cosmetic/usability. Bundle in polish pass.

## 5. Resilience Validation (May 15)

1. Stop Ollama and verify analyze returns user-friendly 503 in UI.
2. Restore Ollama and verify retry recovers.
3. Run scripts/run_resilience_test.bat (Windows) or bash scripts/run_resilience_test.sh.

## 6. Visual Polish Verification (May 16)

- Confirm typography, spacing, and CTA consistency.
- Verify touch targets on 375px viewport.
- Verify no overflow in dashboard tables/map cards.
