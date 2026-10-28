"""Regression tests: history / conversation entry ids must be unique.

The frontend renders ``GameState.history`` and ``ConversationEntry`` lists with
``key={entry.id}``. Those ids used to be ``str(timestamp.timestamp())``, which
collides whenever a producer sends several events inside the same second (a
hook with second precision, or any non-Claude producer replaying a burst).

Duplicate React keys make entries render duplicated or omitted, which surfaced
as ``Encountered two children with the same key`` in the sidebar.
"""

from datetime import UTC, datetime

from app.core.event_processor import EventProcessor
from app.models.events import SessionEvent


def _event(session_id: str = "session_1") -> SessionEvent:
    """Build a minimal event with a fixed, second-precision timestamp."""
    return SessionEvent(
        event_type="session_start",
        session_id=session_id,
        timestamp=datetime(2026, 10, 28, 15, 41, 3, tzinfo=UTC),
        data={},
    )


def test_entry_id_unique_for_events_sharing_a_timestamp() -> None:
    """Ten events at the same timestamp must yield ten distinct entry ids."""
    processor = EventProcessor()
    ids = {processor._entry_id(_event()) for _ in range(10)}
    assert len(ids) == 10


def test_entry_id_keeps_timestamp_prefix() -> None:
    """The timestamp stays in the id so ordering/debugging is unaffected."""
    processor = EventProcessor()
    entry_id = processor._entry_id(_event())
    assert entry_id.startswith("1793202063.0-")


def test_entry_id_suffix_stays_distinct() -> None:
    """Role suffixes (``_tool`` / ``_thinking``) must not collide either."""
    processor = EventProcessor()
    ids = {
        processor._entry_id(_event(), suffix=suffix)
        for suffix in ("", "_tool", "", "_thinking", "")
    }
    assert len(ids) == 5


def test_entry_id_differs_across_sessions() -> None:
    """Two sessions with the same timestamp must still get distinct ids."""
    processor = EventProcessor()
    first = processor._entry_id(_event("session_1"))
    second = processor._entry_id(_event("session_2"))
    assert first != second
