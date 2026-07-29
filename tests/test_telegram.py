from __future__ import annotations

import unittest

from src.config import Config
from src.models import JobOffer
from src.telegram import (
    _split_for_telegram,
    build_message,
    escape_markdown_v2,
    format_offer,
    send_messages,
)


class EscapeTests(unittest.TestCase):
    def test_escapes_specials(self) -> None:
        out = escape_markdown_v2("hello. (world) - test!")
        self.assertEqual(out, "hello\\. \\(world\\) \\- test\\!")

    def test_keeps_plain_text(self) -> None:
        self.assertEqual(escape_markdown_v2("plain text 123"), "plain text 123")

    def test_escapes_url_chars(self) -> None:
        out = escape_markdown_v2("https://example.com/api-v2/path?x=1")
        self.assertIn("\\.", out)
        self.assertIn("\\=", out)
        self.assertIn("\\-", out)


class FormatOfferTests(unittest.TestCase):
    def test_includes_all_fields(self) -> None:
        offer = JobOffer(
            id="1",
            title="Senior Dev",
            company="Acme (Remote)",
            location="EU",
            modality="Remote",
            salary="100k",
            source="remotive",
            url="https://example.com/1)",
            published_at="2024-01-01T00:00:00Z",
        )
        text = format_offer(offer)
        self.assertIn("Senior Dev", text)
        self.assertIn("Acme \\(Remote\\)", text)
        self.assertIn("https://example\\.com/1\\)", text)
        self.assertIn("Salario: 100k", text)
        self.assertIn("🔗 https://example\\.com/1\\)", text)
        self.assertNotIn("[Ver oferta]", text)

    def test_omits_salary_when_none(self) -> None:
        offer = JobOffer(
            id="1",
            title="T",
            company="C",
            location="L",
            modality="Remote",
            salary=None,
            source="s",
            url="u",
            published_at="p",
        )
        text = format_offer(offer)
        self.assertNotIn("Salario:", text)


class BuildMessageTests(unittest.TestCase):
    def test_no_offers(self) -> None:
        self.assertEqual(build_message([], limit=4000), [])

    def test_header_includes_count(self) -> None:
        offer = JobOffer(
            id="1",
            title="t",
            company="c",
            location="l",
            modality="Remote",
            salary=None,
            source="s",
            url="https://e/1",
            published_at="2024-01-01",
        )
        msgs = build_message([offer], limit=4000)
        self.assertEqual(len(msgs), 1)
        self.assertIn("(1)", msgs[0])

    def test_splits_when_exceeds_limit(self) -> None:
        offers = [
            JobOffer(
                id=str(i),
                title=f"Title {i} " + ("x" * 200),
                company="C",
                location="L",
                modality="Remote",
                salary=None,
                source="s",
                url=f"https://e/{i}",
                published_at="2024-01-01",
            )
            for i in range(20)
        ]
        msgs = build_message(offers, limit=1500)
        self.assertGreater(len(msgs), 1)


class SplitTests(unittest.TestCase):
    def test_short_message(self) -> None:
        self.assertEqual(_split_for_telegram("hello", 100), ["hello"])

    def test_splits_long_message(self) -> None:
        text = "line\n" * 200
        parts = _split_for_telegram(text, 50)
        self.assertTrue(all(len(p) <= 50 for p in parts))
        self.assertGreater(len(parts), 1)


class SendDryRunTests(unittest.TestCase):
    def test_dry_run_returns_count_without_http(self) -> None:
        cfg = Config(
            telegram_bot_token=None,
            telegram_chat_id=None,
            dry_run=True,
        )
        count = send_messages(cfg, ["msg1", "msg2"])
        self.assertEqual(count, 2)

    def test_dry_run_with_none_credentials_still_works(self) -> None:
        cfg = Config(
            telegram_bot_token=None,
            telegram_chat_id=None,
            dry_run=True,
        )
        msgs = build_message(
            [
                JobOffer(
                    id="1",
                    title="t",
                    company="c",
                    location="l",
                    modality="Remote",
                    salary=None,
                    source="s",
                    url="https://e/1",
                    published_at="p",
                )
            ],
            limit=4000,
        )
        count = send_messages(cfg, msgs)
        self.assertEqual(count, len(msgs))


if __name__ == "__main__":
    unittest.main()
