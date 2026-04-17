import asyncio
from copy import deepcopy
from datetime import datetime, timezone

from bson import ObjectId

from app.routers import complaints, notifications
from app.schemas import ComplaintStatus, NotificationType, StatusUpdateRequest, UserRole


class _FakeCollection:
    def __init__(self, docs):
        self.docs = [deepcopy(doc) for doc in docs]

    def _matches(self, doc, query):
        for key, value in query.items():
            if isinstance(value, dict) and "$in" in value:
                if doc.get(key) not in value["$in"]:
                    return False
                continue
            if doc.get(key) != value:
                return False
        return True

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if self._matches(doc, query):
                if projection:
                    projected = {}
                    for field, include in projection.items():
                        if include and field in doc:
                            projected[field] = doc[field]
                    return deepcopy(projected)
                return deepcopy(doc)
        return None

    async def find_one_and_update(self, query, update, return_document=True):
        for idx, doc in enumerate(self.docs):
            if not self._matches(doc, query):
                continue
            if "$set" in update:
                for key, value in update["$set"].items():
                    doc[key] = value
            if "$push" in update:
                for key, value in update["$push"].items():
                    doc.setdefault(key, []).append(value)
            self.docs[idx] = doc
            return deepcopy(doc) if return_document else None
        return None

    async def update_many(self, query, update):
        matched = 0
        for idx, doc in enumerate(self.docs):
            if not self._matches(doc, query):
                continue
            matched += 1
            if "$set" in update:
                for key, value in update["$set"].items():
                    doc[key] = value
            self.docs[idx] = doc
        return {"matched_count": matched}

    async def count_documents(self, query):
        count = 0
        for doc in self.docs:
            if self._matches(doc, query):
                count += 1
        return count


class _FakeDB(dict):
    pass


def test_status_update_triggers_notification_and_email(monkeypatch):
    complaint_id = ObjectId()
    citizen_id = ObjectId()
    dept_name = "Municipal - Street Lighting"

    fake_db = _FakeDB(
        {
            "complaints": _FakeCollection(
                [
                    {
                        "_id": complaint_id,
                        "department": dept_name,
                        "status": ComplaintStatus.OPEN,
                        "user_id": str(citizen_id),
                        "status_history": [],
                    }
                ]
            ),
            "users": _FakeCollection([
                {"_id": citizen_id, "email": "citizen@example.com"}
            ]),
            "notifications": _FakeCollection([]),
        }
    )

    monkeypatch.setattr(complaints, "get_database", lambda: fake_db)

    captured = {"notifications": [], "emails": []}

    async def fake_create_notification(**kwargs):
        captured["notifications"].append(kwargs)

    def fake_send_status_update_email(to_email, complaint_id_str, department, status_to, message):
        captured["emails"].append(
            {
                "to_email": to_email,
                "complaint_id": complaint_id_str,
                "department": department,
                "status_to": status_to,
                "message": message,
            }
        )

    monkeypatch.setattr(complaints, "create_notification", fake_create_notification)
    monkeypatch.setattr(complaints, "send_status_update_email", fake_send_status_update_email)

    payload = StatusUpdateRequest(
        status=ComplaintStatus.IN_PROGRESS,
        note="<script>alert('xss')</script>",
    )
    current_user = {
        "_id": str(ObjectId()),
        "role": UserRole.DEPT_HEAD,
        "department": dept_name,
        "username": "dept_head_1",
    }

    updated = asyncio.run(
        complaints.update_complaint_status(
            complaint_id=str(complaint_id),
            payload=payload,
            current_user=current_user,
        )
    )

    status_value = updated["status"].value if hasattr(updated["status"], "value") else updated["status"]
    assert status_value == ComplaintStatus.IN_PROGRESS.value
    assert updated["status_history"]
    assert updated["status_history"][-1]["note"] == "<script>alert('xss')</script>"

    assert len(captured["notifications"]) == 1
    assert captured["notifications"][0]["notification_type"] == NotificationType.STATUS_CHANGE

    assert len(captured["emails"]) == 1
    assert captured["emails"][0]["to_email"] == "citizen@example.com"
    assert "Note: <script>alert('xss')</script>" in captured["emails"][0]["message"]


def test_mark_all_read_clears_unread_badge(monkeypatch):
    user_id = ObjectId()
    fake_db = _FakeDB(
        {
            "notifications": _FakeCollection(
                [
                    {
                        "_id": ObjectId(),
                        "user_id": str(user_id),
                        "is_read": False,
                        "created_at": datetime.now(timezone.utc),
                    },
                    {
                        "_id": ObjectId(),
                        "user_id": str(user_id),
                        "is_read": False,
                        "created_at": datetime.now(timezone.utc),
                    },
                ]
            )
        }
    )

    monkeypatch.setattr(notifications, "get_database", lambda: fake_db)
    current_user = {"_id": user_id}

    before = asyncio.run(notifications.unread_count(current_user=current_user))
    assert before["count"] == 2

    asyncio.run(notifications.mark_all_read(current_user=current_user))

    after = asyncio.run(notifications.unread_count(current_user=current_user))
    assert after["count"] == 0
