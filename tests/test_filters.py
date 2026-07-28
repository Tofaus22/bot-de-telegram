from __future__ import annotations

import unittest

from src.filters import apply_filters
from src.models import JobOffer


def _offer(**kw: object) -> JobOffer:
    base: dict[str, object] = dict(
        id="1",
        title="Senior Backend Developer",
        company="Acme",
        location="Remote, EU",
        modality="Remote",
        salary=None,
        source="test",
        url="https://example.com/1",
        published_at="2024-01-01T00:00:00Z",
    )
    base.update(kw)
    return JobOffer(**base)


class FilterTests(unittest.TestCase):
    def test_accept_remote_with_default(self) -> None:
        res = apply_filters([_offer()], keywords=(), require_remote=True)
        self.assertEqual(len(res.accepted), 1)
        self.assertEqual(res.rejected, [])

    def test_reject_non_remote_when_required(self) -> None:
        res = apply_filters(
            [_offer(modality="Onsite", location="Berlin")],
            keywords=(),
            require_remote=True,
        )
        self.assertEqual(len(res.accepted), 0)
        self.assertEqual(res.rejected[0][1], "not-remote")

    def test_remote_inferred_from_location(self) -> None:
        res = apply_filters(
            [_offer(modality="Onsite", location="Remote, US")],
            keywords=(),
            require_remote=True,
        )
        self.assertEqual(len(res.accepted), 1)

    def test_remote_inferred_from_title(self) -> None:
        res = apply_filters(
            [_offer(modality="Onsite", location="Berlin", title="WFH Backend Dev")],
            keywords=(),
            require_remote=True,
        )
        self.assertEqual(len(res.accepted), 1)

    def test_keyword_filter_case_insensitive(self) -> None:
        offers = [
            _offer(id="1", title="Backend Engineer"),
            _offer(id="2", title="Accountant"),
        ]
        res = apply_filters(offers, keywords=("backend",), require_remote=False)
        self.assertEqual(len(res.accepted), 1)
        self.assertEqual(res.accepted[0].id, "1")
        self.assertEqual(res.rejected[0][1], "keyword-miss")

    def test_keyword_matches_company(self) -> None:
        res = apply_filters(
            [_offer(company="Python Corp")],
            keywords=("python",),
            require_remote=False,
        )
        self.assertEqual(len(res.accepted), 1)

    def test_empty_keywords_accept_all(self) -> None:
        offers = [_offer(), _offer(id="2", title="X")]
        res = apply_filters(offers, keywords=(), require_remote=False)
        self.assertEqual(len(res.accepted), 2)


if __name__ == "__main__":
    unittest.main()
