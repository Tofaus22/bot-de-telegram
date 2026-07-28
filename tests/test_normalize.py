from __future__ import annotations

import unittest

from src.sources.arbeitnow import normalize as arbeitnow_normalize
from src.sources.remotive import normalize as remotive_normalize


class RemotiveNormalizeTests(unittest.TestCase):
    def test_basic(self) -> None:
        raw = {
            "id": 123,
            "title": "Backend Engineer",
            "company_name": "Acme",
            "candidate_required_location": "Worldwide",
            "salary": "100k USD",
            "url": "https://remotive.com/jobs/123",
            "publication_date": "2024-01-15T10:00:00",
        }
        offer = remotive_normalize(raw)
        self.assertEqual(offer.id, "123")
        self.assertEqual(offer.title, "Backend Engineer")
        self.assertEqual(offer.company, "Acme")
        self.assertEqual(offer.location, "Worldwide")
        self.assertEqual(offer.modality, "Remote")
        self.assertEqual(offer.salary, "100k USD")
        self.assertEqual(offer.source, "remotive")
        self.assertEqual(offer.published_at, "2024-01-15T10:00:00")
        self.assertTrue(offer.fingerprint().startswith("remotive|123|"))

    def test_missing_fields(self) -> None:
        raw = {"id": "x", "url": "https://x"}
        offer = remotive_normalize(raw)
        self.assertEqual(offer.title, "(sin título)")
        self.assertEqual(offer.company, "(empresa no especificada)")
        self.assertEqual(offer.location, "Worldwide")
        self.assertIsNone(offer.salary)
        self.assertEqual(offer.published_at, "")

    def test_blank_salary_is_none(self) -> None:
        raw = {"id": "x", "title": "t", "salary": "   "}
        offer = remotive_normalize(raw)
        self.assertIsNone(offer.salary)


class ArbeitnowNormalizeTests(unittest.TestCase):
    def test_remote(self) -> None:
        raw = {
            "slug": "abc",
            "title": "Fullstack Developer",
            "company_name": "Beta",
            "location": "Anywhere",
            "remote": True,
            "url": "https://arbeitnow.com/jobs/abc",
            "created_at": 1700000000,
            "tags": ["python", "django"],
        }
        offer = arbeitnow_normalize(raw)
        self.assertEqual(offer.id, "abc")
        self.assertEqual(offer.title, "Fullstack Developer")
        self.assertEqual(offer.company, "Beta")
        self.assertEqual(offer.modality, "Remote")
        self.assertEqual(offer.source, "arbeitnow")
        self.assertEqual(offer.published_at, "1700000000")
        self.assertEqual(offer.salary, "python, django")

    def test_not_remote(self) -> None:
        raw = {
            "slug": "b",
            "title": "Backend Engineer",
            "company_name": "Y",
            "location": "Berlin",
            "remote": False,
            "url": "u",
            "created_at": 0,
            "tags": [],
        }
        offer = arbeitnow_normalize(raw)
        self.assertEqual(offer.modality, "Onsite")
        self.assertIsNone(offer.salary)


if __name__ == "__main__":
    unittest.main()
