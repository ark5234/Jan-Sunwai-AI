"""
P3-A: LLM job results are now persisted to MongoDB with a TTL index instead of
being stored in a plain Python dict. This survives process restarts, OOM kills,
and rolling redeploys.

The in-process dict used in the original design was lost on any restart — citizens
who submitted a complaint would silently lose their AI-generated draft. Now job
state survives and the frontend can poll reliably.
"""
import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.config import settings
from app.generator import generate_complaint

RESULT_TTL_SECONDS = 3600   # results expire after 1 hour (TTL index on MongoDB)
RESULT_MAX_SIZE = 500        # in-memory cap for the fast-path cache


@dataclass
class LLMJob:
    job_id: str
    image_path: str
    classification: dict[str, Any]
    user_details: dict[str, Any]
    location_details: dict[str, Any]
    language: str = "en"


class LLMQueueService:
    def __init__(self):
        self.queue: asyncio.Queue[LLMJob] = asyncio.Queue()
        # Fast-path in-memory cache (still useful for hot polling within same process)
        self._cache: dict[str, dict[str, Any]] = {}
        self._workers: list[asyncio.Task] = []

    # ------------------------------------------------------------------
    # DB helpers — lazy import to avoid circular dependency at module load
    # ------------------------------------------------------------------

    def _get_db(self):
        """Lazy import of the live DB reference."""
        from app.database import get_database
        return get_database()

    async def _db_upsert(self, job_id: str, doc: dict) -> None:
        """Persist job state to MongoDB. Non-fatal on error."""
        try:
            db = self._get_db()
            await db["llm_jobs"].update_one(
                {"_id": job_id},
                {
                    "$set": doc,
                    "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
                },
                upsert=True,
            )
        except Exception as exc:
            logging.getLogger("JanSunwaiAI.llm_queue").warning(
                "Failed to persist job %s to DB: %s", job_id, exc
            )

    async def _db_get(self, job_id: str, include_private: bool = False) -> dict | None:
        """Read job from MongoDB (fallback when not in cache)."""
        try:
            db = self._get_db()
            doc = await db["llm_jobs"].find_one({"_id": job_id})
            if doc:
                doc.pop("_id", None)
                doc.pop("created_at", None)
                if not include_private:
                    doc.pop("owner_id", None)
                return doc
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # In-memory cache housekeeping (fast-path)
    # ------------------------------------------------------------------

    def _evict(self) -> None:
        """Remove stale in-memory cache entries; enforce MAX_SIZE cap."""
        now = time.monotonic()
        expired = [
            jid for jid, v in self._cache.items()
            if now - v.get("_mono", now) > RESULT_TTL_SECONDS
        ]
        for jid in expired:
            del self._cache[jid]
        if len(self._cache) > RESULT_MAX_SIZE:
            sorted_ids = sorted(self._cache, key=lambda jid: self._cache[jid].get("_mono", 0))
            for jid in sorted_ids[: len(self._cache) - RESULT_MAX_SIZE]:
                del self._cache[jid]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self):
        if self._workers:
            return
        for idx in range(settings.llm_queue_workers):
            task = asyncio.create_task(self._worker_loop(idx + 1))
            self._workers.append(task)

    async def stop(self):
        for task in self._workers:
            task.cancel()
        self._workers.clear()

    # ------------------------------------------------------------------
    # Worker loop
    # ------------------------------------------------------------------

    async def _worker_loop(self, worker_id: int):
        while True:
            job = await self.queue.get()
            self._evict()
            owner_id = str(job.user_details.get("user_id", "") or "")

            initial = {
                "status": "processing",
                "worker_id": worker_id,
                "owner_id": owner_id,
                "_mono": time.monotonic(),
            }
            self._cache[job.job_id] = initial
            await self._db_upsert(
                job.job_id,
                {
                    "status": "processing",
                    "worker_id": worker_id,
                    "owner_id": owner_id,
                },
            )

            try:
                text = await asyncio.to_thread(
                    generate_complaint,
                    job.image_path,
                    job.classification,
                    job.user_details,
                    job.location_details,
                    job.language,
                )
                result = {
                    "status": "completed",
                    "generated_complaint": text,
                    "owner_id": owner_id,
                    "_mono": time.monotonic(),
                }
                self._cache[job.job_id] = result
                await self._db_upsert(
                    job.job_id,
                    {
                        "status": "completed",
                        "generated_complaint": text,
                        "owner_id": owner_id,
                    },
                )
            except Exception as exc:
                logging.getLogger("JanSunwaiAI.llm_queue").exception(
                    "LLM generation failed for job %s", job.job_id
                )
                result = {
                    "status": "failed",
                    "error": "generation_failed",
                    "owner_id": owner_id,
                    "_mono": time.monotonic(),
                }
                self._cache[job.job_id] = result
                await self._db_upsert(
                    job.job_id,
                    {
                        "status": "failed",
                        "error": "generation_failed",
                        "owner_id": owner_id,
                    },
                )
            finally:
                self.queue.task_done()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def enqueue(
        self,
        image_path: str,
        classification: dict[str, Any],
        user_details: dict[str, Any],
        location_details: dict[str, Any],
        language: str = "en",
    ) -> str:
        job_id = str(uuid.uuid4())
        owner_id = str(user_details.get("user_id", "") or "")
        self._evict()
        queued = {"status": "queued", "owner_id": owner_id, "_mono": time.monotonic()}
        self._cache[job_id] = queued
        await self._db_upsert(job_id, {"status": "queued", "owner_id": owner_id})
        await self.queue.put(
            LLMJob(
                job_id=job_id,
                image_path=image_path,
                classification=classification,
                user_details=user_details,
                location_details=location_details,
                language=language,
            )
        )
        return job_id

    def get_result(self, job_id: str) -> dict[str, Any] | None:
        """
        Fast-path: try in-memory cache first, then fall back to DB.
        The sync signature is preserved for backwards compat; DB fallback
        is async but called from sync context via get_result_async() below.
        """
        cached = self._cache.get(job_id)
        if cached:
            out = {k: v for k, v in cached.items() if k not in ("_mono", "owner_id")}
            return out or None
        return None

    async def get_result_async(self, job_id: str, include_private: bool = False) -> dict[str, Any] | None:
        """Async version — checks cache first, then falls back to DB."""
        cached = self._cache.get(job_id)
        if cached:
            if include_private:
                return {k: v for k, v in cached.items() if k not in ("_mono",)}
            out = {k: v for k, v in cached.items() if k not in ("_mono", "owner_id")}
            return out or None
        return await self._db_get(job_id, include_private=include_private)


llm_queue_service = LLMQueueService()
