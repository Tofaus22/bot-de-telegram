from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ..models import JobOffer
from ..utils import http_get_json
from .base import Source

API_URL = "https://www.arbeitnow.com/api/job-board-api"

_DEV_KEYWORDS = (
    "developer",
    "engineer",
    "software",
    "programador",
    "backend",
    "frontend",
    "devops",
    "fullstack",
    "full-stack",
    "full stack",
    "data",
    "sre",
    "qa",
    "mobile",
    "ios",
    "android",
    "web",
    "cloud",
    "platform",
    "machine learning",
    "ml",
    "ai",
    "tech",
)


def _is_dev_offer(item: dict[str, Any]) -> bool:
    tags = item.get("tags") or []
    tag_strs = [str(t).lower() for t in tags] if isinstance(tags, list) else []
    for tag in tag_strs:
        if any(k in tag for k in _DEV_KEYWORDS):
            return True
    title = str(item.get("title", "")).lower()
    return any(k in title for k in _DEV_KEYWORDS)


def _modality(item: dict[str, Any]) -> str:
    if item.get("remote"):
        return "Remote"
    return "Onsite"


def normalize(raw: dict[str, Any]) -> JobOffer:
    salary: str | None = None
    tags = raw.get("tags") or []
    if isinstance(tags, list) and tags:
        salary = ", ".join(str(t) for t in tags)
    return JobOffer(
        id=str(raw.get("slug", "")),
        title=str(raw.get("title", "")).strip() or "(sin título)",
        company=str(raw.get("company_name", "")).strip() or "(empresa no especificada)",
        location=str(raw.get("location", "")).strip() or "Not specified",
        modality=_modality(raw),
        salary=salary,
        source="arbeitnow",
        url=str(raw.get("url", "")).strip(),
        published_at=str(raw.get("created_at", "")),
    )


class ArbeitnowSource(Source):
    name = "arbeitnow"

    def fetch(self) -> Iterable[JobOffer]:
        data = http_get_json(
            API_URL,
            timeout=self.timeout,
            retries=self.retries,
            user_agent=self.user_agent,
        )
        if not isinstance(data, dict):
            return []
        jobs = data.get("data") or []
        if not isinstance(jobs, list):
            return []
        out: list[JobOffer] = []
        for item in jobs:
            if isinstance(item, dict) and _is_dev_offer(item):
                out.append(normalize(item))
        return out
