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


_JUNIOR_INCLUDE_PATTERN = re.compile(
    r"\b(junior|jr\.?|entry[\s\-]?level|graduate|grad|trainee|intern|"
    r"asociate|asociado|sin experiencia|no experience|"
    r"0\s*[-–to]+\s*[1-3]\s*(?:años|years|yrs)?|"
    r"1\s*[-–to]+\s*[1-3]\s*(?:años|years|yrs)?|"
    r"2\s*[-–to]+\s*[1-3]\s*(?:años|years|yrs)?|"
    r"0\s*[-–to]+\s*1\s*(?:año|year|yr)|"
    r"1\s*[-–to]+\s*2\s*(?:años|years|yrs)?)\b",
    re.IGNORECASE,
)


_SENIOR_EXCLUDE_PATTERN = re.compile(
    r"\b(senior|sr\.?|lead|principal|staff|architect|manager|head of|"
    r"director|chief|expert|especialista)\b",
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


def _matches_level(
    offer: JobOffer,
    *,
    include_pattern: re.Pattern[str] | None,
    exclude_pattern: re.Pattern[str],
) -> bool:
    if exclude_pattern.search(offer.title):
        return False
    if include_pattern is None:
        return True
    return bool(include_pattern.search(offer.title))


def apply_filters(
    offers: list[JobOffer],
    *,
    keywords: tuple[str, ...],
    require_remote: bool,
    level_include: re.Pattern[str] | None = None,
    level_exclude: re.Pattern[str] | None = None,
) -> FilterResult:
    accepted: list[JobOffer] = []
    rejected: list[tuple[JobOffer, str]] = []
    exclude = level_exclude or _SENIOR_EXCLUDE_PATTERN
    for offer in offers:
        if require_remote and not _is_remote(offer):
            rejected.append((offer, "not-remote"))
            continue
        if not _matches_keywords(offer, keywords):
            rejected.append((offer, "keyword-miss"))
            continue
        if not _matches_level(offer, include_pattern=level_include, exclude_pattern=exclude):
            rejected.append((offer, "level-miss"))
            continue
        accepted.append(offer)
    return FilterResult(accepted=accepted, rejected=rejected)


def junior_include_pattern() -> re.Pattern[str]:
    return _JUNIOR_INCLUDE_PATTERN


def senior_exclude_pattern() -> re.Pattern[str]:
    return _SENIOR_EXCLUDE_PATTERN
