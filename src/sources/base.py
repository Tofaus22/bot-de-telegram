from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from ..models import JobOffer


class Source(ABC):
    name: str = "source"

    def __init__(self, *, timeout: int, retries: int, user_agent: str) -> None:
        self.timeout = timeout
        self.retries = retries
        self.user_agent = user_agent

    @abstractmethod
    def fetch(self) -> Iterable[JobOffer]:
        ...
