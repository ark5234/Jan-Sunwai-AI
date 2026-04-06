import os
import sys
import time
from typing import Any

import requests


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
CITIZEN_USERNAME = os.getenv("CITIZEN_USERNAME", "citizen1")
CITIZEN_PASSWORD = os.getenv("CITIZEN_PASSWORD", "citizen123")
DEPT_HEAD_USERNAME = os.getenv("DEPT_HEAD_USERNAME", "dept_head1")
DEPT_HEAD_PASSWORD = os.getenv("DEPT_HEAD_PASSWORD", "depthead123")
COMPLAINT_ID = os.getenv("COMPLAINT_ID", "").strip()


class ChainTestError(RuntimeError):
    pass


def _raise_for_status(resp: requests.Response, context: str) -> None:
    if resp.ok:
        return
    raise ChainTestError(f"{context} failed: {resp.status_code} {resp.text}")


def login(username: str, password: str) -> str:
    resp = requests.post(
        f"{API_BASE_URL}/users/login",
        data={"username": username, "password": password},
        timeout=20,
    )
    _raise_for_status(resp, f"login ({username})")
    token = resp.json().get("access_token")
    if not token:
        raise ChainTestError(f"No access token returned for user '{username}'")
    return token


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def get_unread_count(token: str) -> int:
    resp = requests.get(
        f"{API_BASE_URL}/notifications/unread-count",
        headers=auth_headers(token),
        timeout=20,
    )
    _raise_for_status(resp, "unread-count")
    return int(resp.json().get("count", 0))


def choose_complaint_id(citizen_token: str) -> str:
    if COMPLAINT_ID:
        return COMPLAINT_ID
    resp = requests.get(
        f"{API_BASE_URL}/complaints",
        headers=auth_headers(citizen_token),
        timeout=20,
    )
    _raise_for_status(resp, "list complaints")
    items = resp.json()
    if not items:
        raise ChainTestError("No complaints found for citizen. Set COMPLAINT_ID explicitly.")
    return str(items[0].get("_id"))


def patch_status(dept_token: str, complaint_id: str, note: str) -> None:
    resp = requests.patch(
        f"{API_BASE_URL}/complaints/{complaint_id}/status",
        json={"status": "In Progress", "note": note},
        headers=auth_headers(dept_token),
        timeout=30,
    )
    _raise_for_status(resp, "update complaint status")


def fetch_notifications(token: str) -> list[dict[str, Any]]:
    resp = requests.get(
        f"{API_BASE_URL}/notifications?limit=20",
        headers=auth_headers(token),
        timeout=20,
    )
    _raise_for_status(resp, "list notifications")
    payload = resp.json()
    return payload if isinstance(payload, list) else []


def mark_all_read(token: str) -> None:
    resp = requests.patch(
        f"{API_BASE_URL}/notifications/read-all",
        headers=auth_headers(token),
        timeout=20,
    )
    _raise_for_status(resp, "mark-all-read")


def run() -> int:
    print(f"[chain-test] API base: {API_BASE_URL}")
    citizen_token = login(CITIZEN_USERNAME, CITIZEN_PASSWORD)
    dept_token = login(DEPT_HEAD_USERNAME, DEPT_HEAD_PASSWORD)

    complaint_id = choose_complaint_id(citizen_token)
    print(f"[chain-test] Using complaint: {complaint_id}")

    before = get_unread_count(citizen_token)
    print(f"[chain-test] unread before: {before}")

    test_note = f"chain-test-note-{int(time.time())}"
    patch_status(dept_token, complaint_id, test_note)

    after = before
    for _ in range(12):
        time.sleep(1)
        after = get_unread_count(citizen_token)
        if after > before:
            break

    print(f"[chain-test] unread after status update: {after}")
    if after <= before:
        raise ChainTestError("Unread count did not increase after status update")

    notifications = fetch_notifications(citizen_token)
    matching = [
        n for n in notifications
        if str(n.get("complaint_id")) == complaint_id and test_note in (n.get("message") or "")
    ]
    if not matching:
        raise ChainTestError("Notification message for status update note was not found")
    print(f"[chain-test] matching notifications found: {len(matching)}")

    mark_all_read(citizen_token)
    final_count = get_unread_count(citizen_token)
    print(f"[chain-test] unread after mark-all-read: {final_count}")
    if final_count != 0:
        raise ChainTestError("Unread count did not clear after mark-all-read")

    print("[chain-test] PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except ChainTestError as exc:
        print(f"[chain-test] FAIL: {exc}")
        raise SystemExit(1)
