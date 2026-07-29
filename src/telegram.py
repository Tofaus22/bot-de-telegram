from __future__ import annotations

import io
import json
import logging
import sys
import urllib.error
import urllib.request
from collections.abc import Iterable

from .config import Config
from .models import JobOffer

logger = logging.getLogger(__name__)

_MARKDOWN_V2_SPECIAL = set("_*[]()~`>#+-=|{}.!")


def escape_markdown_v2(text: str) -> str:
    return "".join(f"\\{ch}" if ch in _MARKDOWN_V2_SPECIAL else ch for ch in text)


def _markdown_v2_header(count: int) -> str:
    raw = f"Ofertas remotas nuevas ({count})\n\n"
    return "".join(f"\\{ch}" if ch in _MARKDOWN_V2_SPECIAL else ch for ch in raw)


def format_offer(offer: JobOffer) -> str:
    lines: list[str] = [
        f"*{escape_markdown_v2(offer.title)}*",
        f"Empresa: {escape_markdown_v2(offer.company)}",
        f"Ubicación: {escape_markdown_v2(offer.location)}",
        f"Modalidad: {escape_markdown_v2(offer.modality)}",
    ]
    if offer.salary:
        lines.append(f"Salario: {escape_markdown_v2(offer.salary)}")
    lines.append(f"Fuente: {escape_markdown_v2(offer.source)}")
    lines.append(f"Fecha: {escape_markdown_v2(offer.published_at or 'N/D')}")
    lines.append(f"🔗 {escape_markdown_v2(offer.url)}")
    return "\n".join(lines)


def build_message(offers: list[JobOffer], *, limit: int) -> list[str]:
    if not offers:
        return []
    header = _markdown_v2_header(len(offers))
    chunks: list[str] = []
    current = header
    for offer in offers:
        block = format_offer(offer)
        addition = block + "\n\n---\n\n"
        if len(current) + len(addition) > limit and len(current) > len(header):
            chunks.append(current.rstrip())
            current = header + addition
        else:
            current += addition
    if current.strip():
        chunks.append(current.rstrip())
    return chunks


def _split_for_telegram(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]
    out: list[str] = []
    rest = text
    while len(rest) > limit:
        cut = rest.rfind("\n", 0, limit)
        if cut == -1 or cut < limit // 2:
            cut = limit
        out.append(rest[:cut])
        rest = rest[cut:].lstrip("\n")
    if rest:
        out.append(rest)
    return out


def send_messages(config: Config, messages: Iterable[str]) -> int:
    if config.dry_run:
        stdout = sys.stdout
        reconfigure = getattr(stdout, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")
        elif hasattr(stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(stdout.buffer, encoding="utf-8")
        for msg in messages:
            print("--- TELEGRAM (dry-run) ---")
            print(msg)
            print("-------------------------")
        return sum(1 for _ in messages)
    if not config.can_send_telegram():
        raise RuntimeError(
            "Telegram credentials missing; set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID"
        )
    token = config.telegram_bot_token or ""
    chat_id = config.telegram_chat_id or ""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    sent = 0
    for message in messages:
        for part in _split_for_telegram(message, config.telegram_message_limit):
            payload = json.dumps(
                {
                    "chat_id": chat_id,
                    "text": part,
                    "parse_mode": "MarkdownV2",
                    "disable_web_page_preview": True,
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=config.request_timeout) as resp:
                    body = resp.read().decode("utf-8", "replace")
                    if '"ok":false' in body:
                        raise RuntimeError(f"Telegram API error: {body[:300]}")
            except urllib.error.HTTPError as exc:
                err_body = exc.read().decode("utf-8", "replace") if hasattr(exc, "read") else ""
                logger.error("Telegram HTTP %s: %s", exc.code, err_body[:300])
                raise
            except (urllib.error.URLError, TimeoutError) as exc:
                logger.error("Telegram send failed: %s", exc)
                raise
            sent += 1
    return sent
