import asyncio
import uuid
from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.generator import generate_complaint


@dataclass
class LLMJob:
    job_id: str
    image_path: str
    classification: dict[str, Any]
    user_details: dict[str, Any]
    location_details: dict[str, Any]


class LLMQueueService:
    def __init__(self):
        self.queue: asyncio.Queue[LLMJob] = asyncio.Queue()
        self.results: dict[str, dict[str, Any]] = {}
        self._workers: list[asyncio.Task] = []

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
            self.results[job.job_id] = {"status": "processing", "worker_id": worker_id}
            try:
                text = await asyncio.to_thread(
                    generate_complaint,
                    job.image_path,
                    job.classification,
                    job.user_details,
                    job.location_details,
                )
                self.results[job.job_id] = {
                    "status": "completed",
                    "generated_complaint": text,
                }
            except Exception as exc:
                self.results[job.job_id] = {
                    "status": "failed",
                    "error": str(exc),
                }
            finally:
                self.queue.task_done()

    async def enqueue(self, image_path: str, classification: dict[str, Any], user_details: dict[str, Any], location_details: dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        self.results[job_id] = {"status": "queued"}
        await self.queue.put(
            LLMJob(
                job_id=job_id,
                image_path=image_path,
                classification=classification,
                user_details=user_details,
                location_details=location_details,
            )
        )
        return job_id

    def get_result(self, job_id: str) -> dict[str, Any] | None:
        return self.results.get(job_id)


llm_queue_service = LLMQueueService()
