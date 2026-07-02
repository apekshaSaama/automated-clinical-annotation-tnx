import os
import urllib.error
import urllib.request
import json
from typing import Any


class OpenMedGlinerBiomedicalConnector:
    """Connector for calling the OpenMed GLiNER biomedical model via HTTP."""

    def __init__(self, endpoint: str | None = None, timeout: int = 60):
        self.endpoint = (endpoint or os.environ.get("OPENMED_ENDPOINT") or "").rstrip("/")
        self.timeout = timeout

        if not self.endpoint:
            raise ValueError("OPENMED_ENDPOINT is required")

    def invoke(self, text: str, labels: list[str] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"text": text}
        if labels:
            payload["labels"] = labels

        request = urllib.request.Request(
            url=self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                return json.loads(body)
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenMed request failed ({exc.code}): {error_body}") from exc
