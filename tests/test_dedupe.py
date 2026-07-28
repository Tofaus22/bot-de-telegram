from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.dedupe import MAX_SEEN, State, load_state, mark_many, select_new
from src.models import JobOffer


def _offer(slug: str) -> JobOffer:
    return JobOffer(
        id=slug,
        title="T",
        company="C",
        location="Remote",
        modality="Remote",
        salary=None,
        source="test",
        url=f"https://x/{slug}",
        published_at="2024-01-01T00:00:00Z",
    )


class DedupeTests(unittest.TestCase):
    def test_select_new_returns_unique_unseen(self) -> None:
        state = State()
        out = select_new(
            [_offer("a"), _offer("b"), _offer("a"), _offer("c"), _offer("b")],
            state,
        )
        self.assertEqual([o.id for o in out], ["a", "b", "c"])
        self.assertEqual(len(state.seen), 0)

    def test_select_new_dedupes_within_run(self) -> None:
        state = State()
        out = select_new(
            [_offer("a"), _offer("a"), _offer("b"), _offer("b")],
            state,
        )
        self.assertEqual([o.id for o in out], ["a", "b"])

    def test_select_new_combines_state_and_run(self) -> None:
        state = State()
        state.mark(_offer("a").fingerprint())
        out = select_new(
            [_offer("a"), _offer("b"), _offer("b"), _offer("c")],
            state,
        )
        self.assertEqual([o.id for o in out], ["b", "c"])

    def test_select_new_skips_seen(self) -> None:
        state = State()
        state.mark(_offer("a").fingerprint())
        out = select_new([_offer("a"), _offer("b")], state)
        self.assertEqual([o.id for o in out], ["b"])

    def test_mark_many(self) -> None:
        state = State()
        mark_many(state, [_offer("a"), _offer("b")])
        self.assertTrue(state.is_seen(_offer("a").fingerprint()))
        self.assertTrue(state.is_seen(_offer("b").fingerprint()))

    def test_save_and_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            state = State(path=path)
            mark_many(state, [_offer("a"), _offer("b")])
            state.save()
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn(_offer("a").fingerprint(), data["seen"])
            self.assertIn(_offer("b").fingerprint(), data["seen"])
            loaded = load_state(path)
            self.assertTrue(loaded.is_seen(_offer("a").fingerprint()))
            self.assertTrue(loaded.is_seen(_offer("b").fingerprint()))

    def test_max_seen_cap_drops_oldest(self) -> None:
        state = State()
        for i in range(MAX_SEEN + 100):
            mark_many(state, [_offer(f"id-{i}")])
        self.assertEqual(len(state.seen), MAX_SEEN)
        self.assertFalse(state.is_seen(_offer("id-0").fingerprint()))
        self.assertTrue(state.is_seen(_offer(f"id-{MAX_SEEN + 99}").fingerprint()))

    def test_unreadable_state_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            path.write_text("{not json", encoding="utf-8")
            state = load_state(path)
            self.assertEqual(len(state.seen), 0)

    def test_missing_state_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = load_state(Path(tmp) / "nope.json")
            self.assertEqual(len(state.seen), 0)


if __name__ == "__main__":
    unittest.main()
