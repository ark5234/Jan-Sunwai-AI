import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.config import settings
from app.generator import generate_complaint

RESULT_TTL_SECONDS = 600   # results expire after 10 minutes
RESULT_MAX_SIZE = 500      # max entries before forced eviction


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
        # results: {job_id: {"status": ..., "stored_at": float, ...}}
        self.results: dict[str, dict[str, Any]] = {}
        self._workers: list[asyncio.Task] = []

    def _evict(self) -> None:
        """Remove expired entries (TTL) and enforce MAX_SIZE cap."""
        now = time.monotonic()
        # Drop entries older than TTL
        expired = [
            jid for jid, v in self.results.items()
            if now - v.get("stored_at", now) > RESULT_TTL_SECONDS
        ]
        for jid in expired:
            del self.results[jid]
        # If still over limit, evict oldest by stored_at
        if len(self.results) > RESULT_MAX_SIZE:
            sorted_ids = sorted(
                self.results, key=lambda jid: self.results[jid].get("stored_at", 0)
            )
            for jid in sorted_ids[: len(self.results) - RESULT_MAX_SIZE]:
                del self.results[jid]

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

    async def _worker_loop(self, worker_id: int):
        while True:
            job = await self.queue.get()
            self._evict()  # housekeeping on each dequeue
            self.results[job.job_id] = {"status": "processing", "worker_id": worker_id, "stored_at": time.monotonic()}
            try:
                text = await asyncio.to_thread(
                    generate_complaint,
                    job.image_path,
                    job.classification,
                    job.user_details,
                    job.location_details,
                    job.language,
                )
                self.results[job.job_id] = {
                    "status": "completed",
                    "generated_complaint": text,
                    "stored_at": time.monotonic(),
                }
            except Exception as exc:
                self.results[job.job_id] = {
                    "status": "failed",
                    "error": str(exc),
                    "stored_at": time.monotonic(),
                }
            finally:
                self.queue.task_done()

    async def enqueue(self, image_path: str, classification: dict[str, Any], user_details: dict[str, Any], location_details: dict[str, Any], language: str = "en") -> str:
        job_id = str(uuid.uuid4())
        self._evict()  # housekeeping before adding
        self.results[job_id] = {"status": "queued", "stored_at": time.monotonic()}
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
        return self.results.get(job_id)


llm_queue_service = LLMQueueService()
