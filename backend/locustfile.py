import io
import os

from locust import HttpUser, between, task
from PIL import Image


CITIZEN_USERNAME = os.getenv("LOCUST_CITIZEN_USERNAME", "citizen1")
CITIZEN_PASSWORD = os.getenv("LOCUST_CITIZEN_PASSWORD", "citizen123")


def _make_image_payload() -> bytes:
    img = Image.new("RGB", (128, 128), color=(150, 150, 150))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class JanSunwaiUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.citizen_token = self._login(CITIZEN_USERNAME, CITIZEN_PASSWORD)
        self.sample_image = _make_image_payload()

    def _login(self, username: str, password: str) -> str:
        response = self.client.post(
            "/api/v1/users/login",
            data={"username": username, "password": password},
            name="/api/v1/users/login",
        )
        if response.status_code != 200:
            return ""
        return response.json().get("access_token", "")

    @task(4)
    def public_status(self):
        with self.client.get("/api/v1/public/complaints", name="/api/v1/public/complaints", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(3)
    def health_live(self):
        with self.client.get("/api/v1/health/live", name="/api/v1/health/live", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(2)
    def unread_count(self):
        if not self.citizen_token:
            return
        with self.client.get(
            "/api/v1/notifications/unread-count",
            headers={"Authorization": f"Bearer {self.citizen_token}"},
            name="/api/v1/notifications/unread-count",
            catch_response=True,
        ) as response:
            if response.status_code not in (200, 401):
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(1)
    def analyze_upload(self):
        if not self.citizen_token:
            return

        files = {
            "file": ("locust-load.jpg", self.sample_image, "image/jpeg"),
        }
        data = {"language": "en"}

        with self.client.post(
            "/api/v1/analyze",
            headers={"Authorization": f"Bearer {self.citizen_token}"},
            files=files,
            data=data,
            name="/api/v1/analyze",
            catch_response=True,
        ) as response:
            # Under load we can see throttling (429) or temporary AI unavailability (503).
            if response.status_code not in (200, 429, 503):
                response.failure(f"Unexpected status code: {response.status_code}")
