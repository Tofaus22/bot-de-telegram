from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from .models import JobOffer

logger = logging.getLogger(__name__)

MAX_SEEN = 5000


@dataclass
class State:
    seen: set[str] = field(default_factory=set)
    order: list[str] = field(default_factory=list)
    path: Path | None = None

    def is_seen(self, fp: str) -> bool:
        return fp in self.seen

    def mark(self, fp: str) -> None:
        if fp in self.seen:
            return
        self.seen.add(fp)
        self.order.append(fp)
        if len(self.order) > MAX_SEEN:
            excess = len(self.order) - MAX_SEEN
            for old in self.order[:excess]:
                self.seen.discard(old)
            self.order = self.order[excess:]

    def save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(
            json.dumps({"seen": self.order}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(self.path)


def load_state(path: Path) -> State:
    state = State(path=path)
    if not path.exists():
        return state
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("State file %s unreadable: %s", path, exc)
        return state
    items = raw.get("seen") if isinstance(raw, dict) else None
    if not isinstance(items, list):
        return state
    for item in items:
        if isinstance(item, str):
            state.mark(item)
    return state


def select_new(offers: Iterable[JobOffer], state: State) -> list[JobOffer]:
    out: list[JobOffer] = []
    seen_in_run: set[str] = set()
    for offer in offers:
        fp = offer.fingerprint()
        if state.is_seen(fp) or fp in seen_in_run:
            continue
        seen_in_run.add(fp)
        out.append(offer)
    return out


def mark_many(state: State, offers: Iterable[JobOffer]) -> None:
    for offer in offers:
        state.mark(offer.fingerprint())
