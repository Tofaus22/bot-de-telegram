from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)


class HttpError(Exception):
    def __init__(self, url: str, status: int | None, message: str) -> None:
        super().__init__(f"{url}: {status or 'ERR'} {message}")
        self.url = url
        self.status = status
        self.message = message


def http_get_json(url: str, *, timeout: int, retries: int, user_agent: str) -> Any:
    attempt = 0
    last_error: Exception | None = None
    total = max(retries, 1)
    while attempt < total:
        attempt += 1
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": user_agent,
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
                status = getattr(resp, "status", 200)
                if status >= 400:
                    raise HttpError(url, status, body[:200].decode("utf-8", "replace"))
                return json.loads(body.decode("utf-8", "replace"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            logger.warning("HTTP attempt %d/%d failed for %s: %s", attempt, total, url, exc)
            if attempt < total:
                time.sleep(min(2 ** attempt, 8))
    raise HttpError(url, None, str(last_error) if last_error else "unknown")
