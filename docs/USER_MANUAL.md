# Jan-Sunwai AI User Manual

## 1. Citizen Guide

## Register and Login

1. Open the home page.
2. Select Register and create account.
3. Login with your credentials.

## File a Complaint

1. Go to Analyze.
2. Upload a JPG/PNG image (up to 5 MB).
3. Select preferred language.
4. Click Analyze and Generate Complaint.
5. Review auto-detected department and location.
6. Edit generated complaint text if needed.
7. Submit.

## Track Complaint

1. Open Dashboard.
2. View status (Open, In Progress, Resolved, Rejected).
3. Open timeline for status history and notes.
4. Read notifications from navbar bell icon.

## 2. Department Head Guide

1. Login as department head.
2. Open dashboard and filter departmental complaints.
3. Update complaint status with note.
4. Transfer complaint when required.
5. Review SLA badges and overdue items.

## 3. Worker Guide

1. Register as worker and await admin approval.
2. Login and open Worker Dashboard.
3. Set availability status.
4. Complete assigned complaints and submit work notes.

## 4. Admin Guide

1. Login as admin.
2. Approve/reject worker registrations.
3. Reassign unassigned complaints.
4. Use bulk status/transfer operations.
5. Export CSV reports.
6. Review heatmap and analytics.

## 5. Password Reset

1. Use Forgot Password on login page.
2. Submit registered email.
3. Use received reset token in Reset Password flow.

## 6. Troubleshooting

- Analyze returns 503: ensure Ollama is running and models are loaded.
- Login issues: verify JWT secret and token expiry settings in backend/.env.
- Notifications not updating: run scripts/run_notification_chain_test.
- Map not loading: verify internet access for map tiles or provider key.
