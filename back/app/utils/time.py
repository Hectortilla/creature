"""Time helpers."""

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Naive UTC timestamp — a non-deprecated drop-in for ``datetime.utcnow()``.

    Returns a timezone-*naive* datetime at UTC (``tzinfo=None``), identical to the
    value the deprecated ``datetime.utcnow()`` produced. Keeping it naive means
    serialized wire formats (``.isoformat()``) and DB column values are unchanged;
    migrating to timezone-aware datetimes is a separate, opt-in change.
    """
    return datetime.now(UTC).replace(tzinfo=None)
