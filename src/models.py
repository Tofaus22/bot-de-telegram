from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JobOffer:
    id: str
    title: str
    company: str
    location: str
    modality: str
    salary: str | None
    source: str
    url: str
    published_at: str

    def fingerprint(self) -> str:
        return f"{self.source}|{self.id}|{self.url}".lower()
