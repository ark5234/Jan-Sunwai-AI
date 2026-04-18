#!/usr/bin/env python3
"""
Cookie-session end-to-end smoke test.

Validates this live runtime flow against /api/v1:
1) login (citizen/admin/worker)
2) citizen complaint creation
3) admin manual assignment
4) worker marks complaint done
5) citizen notification visibility
6) admin triage decision and queue removal

This script is intentionally read/write at the application level (it creates one
real complaint and processes it) but does not modify application code.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests


class SmokeTestError(RuntimeError):
    pass


def _normalize_api_base(raw: str) -> str:
    base = (raw or "http://localhost:8000").strip().rstrip("/")
    if base.endswith("/api/v1"):
        return base
    return f"{base}/api/v1"


API_BASE_URL = _normalize_api_base(os.getenv("API_BASE_URL", "http://localhost:8000"))

CITIZEN_USERNAME = os.getenv("SMOKE_CITIZEN_USERNAME", "citizen_demo")
CITIZEN_PASSWORD = os.getenv("SMOKE_CITIZEN_PASSWORD", "citizen123")
ADMIN_USERNAME = os.getenv("SMOKE_ADMIN_USERNAME", "admin_demo")
ADMIN_PASSWORD = os.getenv("SMOKE_ADMIN_PASSWORD", "admin123")
WORKER_USERNAME = os.getenv("SMOKE_WORKER_USERNAME", "civil_sengineer")
WORKER_PASSWORD = os.getenv("SMOKE_WORKER_PASSWORD", "civil123")

SMOKE_DEPARTMENT = os.getenv("SMOKE_DEPARTMENT", "Civil Department")
SMOKE_IMAGE_URL = os.getenv("SMOKE_IMAGE_URL", "").strip()

POLL_ATTEMPTS = int(os.getenv("SMOKE_POLL_ATTEMPTS", "12"))
POLL_INTERVAL_SEC = float(os.getenv("SMOKE_POLL_INTERVAL_SEC", "1"))
HTTP_TIMEOUT_SEC = int(os.getenv("SMOKE_HTTP_TIMEOUT_SEC", "30"))


class Recorder:
    def __init__(self) -> None:
        self.results: list[dict[str, Any]] = []

    def step(self, name: str, ok: bool, detail: str) -> None:
        self.results.append({"step": name, "ok": bool(ok), "detail": detail})
        tag = "PASS" if ok else "FAIL"
        print(f"[{tag}] {name}: {detail}")

    def must(self, name: str, ok: bool, detail: str) -> None:
        self.step(name, ok, detail)
        if not ok:
            raise SmokeTestError(f"{name} failed: {detail}")


def _json_or_text(resp: requests.Response) -> str:
    try:
        return json.dumps(resp.json(), ensure_ascii=True)[:220]
    except Exception:
        return (resp.text or "")[:220]


def _login(session: requests.Session, username: str, password: str, label: str, rec: Recorder) -> None:
    resp = session.post(
        f"{API_BASE_URL}/users/login",
        data={"username": username, "password": password},
        timeout=HTTP_TIMEOUT_SEC,
    )
    has_cookie = "js_access_token" in session.cookies.get_dict()
    rec.must(
        f"login:{label}",
        resp.status_code == 200 and has_cookie,
        f"status={resp.status_code}; cookie={'yes' if has_cookie else 'no'}; body={_json_or_text(resp)}",
    )


def _pick_image_url(citizen: requests.Session, rec: Recorder) -> str:
    if SMOKE_IMAGE_URL:
        rec.step("prepare:image-source", True, f"env_override={SMOKE_IMAGE_URL}")
        return SMOKE_IMAGE_URL

    complaints_resp = citizen.get(f"{API_BASE_URL}/complaints", timeout=HTTP_TIMEOUT_SEC)
    if complaints_resp.status_code == 200:
        items = complaints_resp.json() if isinstance(complaints_resp.json(), list) else []
        for item in items:
            image_url = str(item.get("image_url") or "").strip()
            if image_url:
                rec.step("prepare:image-source", True, f"from_existing_complaint={image_url}")
                return image_url

    repo_root = Path(__file__).resolve().parents[1]
    uploads_dir = repo_root / "backend" / "uploads"
    if uploads_dir.exists():
        candidates = sorted(p.name for p in uploads_dir.iterdir() if p.is_file())
        if candidates:
            chosen = f"uploads/{candidates[0]}"
            rec.step("prepare:image-source", True, f"from_uploads_dir={chosen}")
            return chosen

    rec.must(
        "prepare:image-source",
        False,
        "No image source found. Set SMOKE_IMAGE_URL to an existing uploads path.",
    )
    return ""


def run() -> int:
    rec = Recorder()
    complaint_id: str | None = None

    citizen = requests.Session()
    admin = requests.Session()
    worker = requests.Session()

    try:
        _login(citizen, CITIZEN_USERNAME, CITIZEN_PASSWORD, CITIZEN_USERNAME, rec)

        me_resp = citizen.get(f"{API_BASE_URL}/users/me", timeout=HTTP_TIMEOUT_SEC)
        me_user = me_resp.json().get("username") if me_resp.status_code == 200 else None
        rec.must("citizen:users/me", me_resp.status_code == 200, f"status={me_resp.status_code}; user={me_user}")

        unread_before_resp = citizen.get(f"{API_BASE_URL}/notifications/unread-count", timeout=HTTP_TIMEOUT_SEC)
        rec.must("citizen:unread-count(before)", unread_before_resp.status_code == 200, f"status={unread_before_resp.status_code}")
        unread_before = int(unread_before_resp.json().get("count", 0))

        image_url = _pick_image_url(citizen, rec)

        now = int(time.time())
        complaint_payload = {
            "description": f"Smoke test complaint {now}: cookie-auth runtime verification.",
            "department": SMOKE_DEPARTMENT,
            "user_grievance_text": "Infrastructure issue observed and needs civil action.",
            "image_url": image_url,
            "location": {
                "lat": 28.6145,
                "lon": 77.2075,
                "address": "Outer Circle, Connaught Place, New Delhi",
                "source": "manual",
            },
            "ai_metadata": {
                "model_used": "smoke-test",
                "confidence_score": 0.41,
                "detected_department": SMOKE_DEPARTMENT,
                "labels": [SMOKE_DEPARTMENT, "Smoke Test"],
            },
            "language": "en",
        }

        create_resp = citizen.post(
            f"{API_BASE_URL}/complaints",
            json=complaint_payload,
            timeout=HTTP_TIMEOUT_SEC,
        )
        rec.must("citizen:create-complaint", create_resp.status_code == 200, f"status={create_resp.status_code}; body={_json_or_text(create_resp)}")

        created = create_resp.json() if create_resp.status_code == 200 else {}
        complaint_id = str(created.get("_id") or "").strip()
        rec.must("citizen:create-complaint:id", bool(complaint_id), f"complaint_id={complaint_id}")

        _login(admin, ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_USERNAME, rec)

        workers_resp = admin.get(f"{API_BASE_URL}/workers", timeout=HTTP_TIMEOUT_SEC)
        rec.must("admin:list-workers", workers_resp.status_code == 200, f"status={workers_resp.status_code}")
        workers = workers_resp.json() if workers_resp.status_code == 200 else []

        target_worker = next(
            (w for w in workers if w.get("username") == WORKER_USERNAME and w.get("is_approved")),
            None,
        )
        if not target_worker:
            target_worker = next(
                (
                    w
                    for w in workers
                    if w.get("is_approved")
                    and str(w.get("department") or "").strip().lower() == SMOKE_DEPARTMENT.lower()
                ),
                None,
            )

        rec.must("admin:target-worker", target_worker is not None, f"worker_username={WORKER_USERNAME}; found={'yes' if target_worker else 'no'}")
        worker_id = str(target_worker.get("_id"))

        assign_resp = admin.post(
            f"{API_BASE_URL}/workers/{worker_id}/assign/{complaint_id}",
            timeout=HTTP_TIMEOUT_SEC,
        )
        rec.must("admin:manual-assign", assign_resp.status_code == 200, f"status={assign_resp.status_code}; body={_json_or_text(assign_resp)}")

        _login(worker, WORKER_USERNAME, WORKER_PASSWORD, WORKER_USERNAME, rec)

        worker_me_resp = worker.get(f"{API_BASE_URL}/workers/me", timeout=HTTP_TIMEOUT_SEC)
        rec.must("worker:workers/me", worker_me_resp.status_code == 200, f"status={worker_me_resp.status_code}")
        worker_me = worker_me_resp.json() if worker_me_resp.status_code == 200 else {}

        active_ids = set(worker_me.get("active_complaint_ids") or [])
        active_docs = {c.get("_id") for c in (worker_me.get("active_complaints") or []) if c.get("_id")}
        assigned_visible = complaint_id in active_ids or complaint_id in active_docs
        rec.must(
            "worker:assignment-visible",
            assigned_visible,
            f"in_active_ids={complaint_id in active_ids}; in_active_complaints={complaint_id in active_docs}",
        )

        done_resp = worker.patch(
            f"{API_BASE_URL}/workers/me/complaints/{complaint_id}/done",
            timeout=HTTP_TIMEOUT_SEC,
        )
        rec.must("worker:mark-done", done_resp.status_code == 200, f"status={done_resp.status_code}; body={_json_or_text(done_resp)}")

        unread_after = unread_before
        for _ in range(POLL_ATTEMPTS):
            time.sleep(POLL_INTERVAL_SEC)
            poll_resp = citizen.get(f"{API_BASE_URL}/notifications/unread-count", timeout=HTTP_TIMEOUT_SEC)
            if poll_resp.status_code == 200:
                unread_after = int(poll_resp.json().get("count", unread_before))
                if unread_after > unread_before:
                    break

        rec.must(
            "citizen:unread-count(after)",
            unread_after > unread_before,
            f"before={unread_before}; after={unread_after}",
        )

        notif_resp = citizen.get(f"{API_BASE_URL}/notifications?limit=50", timeout=HTTP_TIMEOUT_SEC)
        rec.must("citizen:list-notifications", notif_resp.status_code == 200, f"status={notif_resp.status_code}")
        notifications = notif_resp.json() if notif_resp.status_code == 200 else []
        related = [n for n in notifications if str(n.get("complaint_id")) == complaint_id]
        rec.must("citizen:related-notification", len(related) > 0, f"matches={len(related)}")

        triage_before_resp = admin.get(f"{API_BASE_URL}/triage/review-queue?limit=200", timeout=HTTP_TIMEOUT_SEC)
        rec.must("admin:triage-queue(before)", triage_before_resp.status_code == 200, f"status={triage_before_resp.status_code}")
        before_items = (triage_before_resp.json() or {}).get("items", []) if triage_before_resp.status_code == 200 else []
        rec.must(
            "admin:triage-item-present(before)",
            any(i.get("id") == complaint_id for i in before_items),
            f"queue_items={len(before_items)}",
        )

        triage_post_resp = admin.post(
            f"{API_BASE_URL}/triage/review-queue/decision",
            json={
                "image": complaint_id,
                "decision": "approve",
                "corrected_label": SMOKE_DEPARTMENT,
                "note": "Cookie smoke test decision",
            },
            timeout=HTTP_TIMEOUT_SEC,
        )
        rec.must(
            "admin:triage-decision(post)",
            triage_post_resp.status_code == 200,
            f"status={triage_post_resp.status_code}; body={_json_or_text(triage_post_resp)}",
        )

        time.sleep(POLL_INTERVAL_SEC)
        triage_after_resp = admin.get(f"{API_BASE_URL}/triage/review-queue?limit=200", timeout=HTTP_TIMEOUT_SEC)
        rec.must("admin:triage-queue(after)", triage_after_resp.status_code == 200, f"status={triage_after_resp.status_code}")
        after_items = (triage_after_resp.json() or {}).get("items", []) if triage_after_resp.status_code == 200 else []
        rec.must(
            "admin:triage-item-removed(after)",
            not any(i.get("id") == complaint_id for i in after_items),
            f"queue_before={len(before_items)}; queue_after={len(after_items)}",
        )

        citizen.patch(f"{API_BASE_URL}/notifications/read-all", timeout=HTTP_TIMEOUT_SEC)

        print("\nSMOKE_SUMMARY_JSON_START")
        print(json.dumps({"ok": True, "complaint_id": complaint_id, "results": rec.results}, indent=2))
        print("SMOKE_SUMMARY_JSON_END")
        return 0

    except Exception as exc:
        print("\nSMOKE_SUMMARY_JSON_START")
        print(json.dumps({"ok": False, "error": str(exc), "complaint_id": complaint_id, "results": rec.results}, indent=2))
        print("SMOKE_SUMMARY_JSON_END")
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
