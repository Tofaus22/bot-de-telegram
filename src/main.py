from __future__ import annotations

import logging
import sys
from collections.abc import Iterable

from .config import Config
from .dedupe import load_state, mark_many, select_new
from .filters import apply_filters
from .models import JobOffer
from .sources.arbeitnow import ArbeitnowSource
from .sources.base import Source
from .sources.remotive import RemotiveSource
from .telegram import build_message, send_messages

logger = logging.getLogger(__name__)


def build_sources(config: Config) -> list[Source]:
    return [
        RemotiveSource(
            timeout=config.request_timeout,
            retries=config.request_retries,
            user_agent=config.user_agent,
        ),
        ArbeitnowSource(
            timeout=config.request_timeout,
            retries=config.request_retries,
            user_agent=config.user_agent,
        ),
    ]


def collect(config: Config, sources: Iterable[Source]) -> list[JobOffer]:
    all_offers: list[JobOffer] = []
    for source in sources:
        try:
            fetched = list(source.fetch())
        except Exception as exc:
            logger.exception("Source %s failed: %s", source.name, exc)
            continue
        logger.info("Source %s returned %d offers", source.name, len(fetched))
        all_offers.extend(fetched)
    return all_offers


def run() -> int:
    config = Config.from_env()
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger.info("Starting bot (dry_run=%s)", config.dry_run)
    state = load_state(config.state_path)
    sources = build_sources(config)
    offers = collect(config, sources)
    filtered = apply_filters(
        offers,
        keywords=config.keywords,
        require_remote=config.require_remote,
    )
    logger.info(
        "Filtered: %d accepted, %d rejected",
        len(filtered.accepted),
        len(filtered.rejected),
    )
    fresh = select_new(filtered.accepted, state)
    logger.info("New offers after dedupe: %d", len(fresh))
    if not fresh:
        state.save()
        logger.info("Nothing new to send")
        return 0
    fresh = fresh[: config.max_offers_per_run]
    messages = build_message(fresh, limit=config.telegram_message_limit)
    try:
        sent = send_messages(config, messages)
    except Exception as exc:
        logger.exception("Telegram send failed: %s", exc)
        state.save()
        return 1
    mark_many(state, fresh)
    state.save()
    logger.info("Sent %d telegram message(s)", sent)
    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
