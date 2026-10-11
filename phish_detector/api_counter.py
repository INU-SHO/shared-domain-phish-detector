import contextvars
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator


@dataclass
class ApiCounts:
    vision: int = 0
    cse: int = 0


_current: contextvars.ContextVar[ApiCounts | None] = contextvars.ContextVar(
    "phish_detector_api_counts", default=None
)


@contextmanager
def track_api_calls() -> "Iterator[ApiCounts]":
    counts = ApiCounts()
    token = _current.set(counts)
    try:
        yield counts
    finally:
        _current.reset(token)


def increment_vision() -> None:
    counts = _current.get()
    if counts is not None:
        counts.vision += 1


def increment_cse() -> None:
    counts = _current.get()
    if counts is not None:
        counts.cse += 1
