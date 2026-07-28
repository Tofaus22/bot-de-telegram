from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ..models import JobOffer
from ..utils import http_get_json
from .base import Source

API_URL = "https://remotive.com/api/remote-jobs?category=software-dev"


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize(raw: dict[str, Any]) -> JobOffer:
    salary_value = raw.get("salary")
    salary: str | None = None
    if isinstance(salary_value, str):
        salary_value = salary_value.strip()
        if salary_value:
            salary = salary_value
    return JobOffer(
        id=str(raw.get("id", "")),
        title=_clean(raw.get("title")) or "(sin título)",
        company=_clean(raw.get("company_name")) or "(empresa no especificada)",
        location=_clean(raw.get("candidate_required_location")) or "Worldwide",
        modality="Remote",
        salary=salary,
        source="remotive",
        url=_clean(raw.get("url")),
        published_at=_clean(raw.get("publication_date")),
    )


class RemotiveSource(Source):
    name = "remotive"

    def fetch(self) -> Iterable[JobOffer]:
        data = http_get_json(
            API_URL,
            timeout=self.timeout,
            retries=self.retries,
            user_agent=self.user_agent,
        )
        if not isinstance(data, dict):
            return []
        jobs = data.get("jobs") or []
        if not isinstance(jobs, list):
            return []
        out: list[JobOffer] = []
        for item in jobs:
            if isinstance(item, dict):
                out.append(normalize(item))
        return out
