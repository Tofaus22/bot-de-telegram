from __future__ import annotations

import re
from dataclasses import dataclass

from .models import JobOffer


@dataclass(frozen=True)
class FilterResult:
    accepted: list[JobOffer]
    rejected: list[tuple[JobOffer, str]]


_REMOTE_PATTERN = re.compile(
    r"\b(remote|remoto|teletrabajo|work\s*from\s*home|wfh)\b",
    re.IGNORECASE,
)


def _is_remote(offer: JobOffer) -> bool:
    if offer.modality.lower().startswith("remote"):
        return True
    haystack = f"{offer.location} {offer.title} {offer.company}"
    return bool(_REMOTE_PATTERN.search(haystack))


def _matches_keywords(offer: JobOffer, keywords: tuple[str, ...]) -> bool:
    if not keywords:
        return True
    haystack = " ".join((offer.title, offer.company, offer.location)).lower()
    return any(kw in haystack for kw in keywords)


def apply_filters(
    offers: list[JobOffer],
    *,
    keywords: tuple[str, ...],
    require_remote: bool,
) -> FilterResult:
    accepted: list[JobOffer] = []
    rejected: list[tuple[JobOffer, str]] = []
    for offer in offers:
        if require_remote and not _is_remote(offer):
            rejected.append((offer, "not-remote"))
            continue
        if not _matches_keywords(offer, keywords):
            rejected.append((offer, "keyword-miss"))
            continue
        accepted.append(offer)
    return FilterResult(accepted=accepted, rejected=rejected)
