"""Turning an answer into marks. No Streamlit here, so this is testable on its own.

The patterns come from the published mark schemes: a sample is marked on the
values obtained with a partial-credit ladder, a single stated value (an
interval, a count) carries its own mark, and a set of counts scores in full
when they are all right.
"""

from dataclasses import dataclass, field
from typing import Any, List, Sequence


@dataclass
class Award:
    """A mark, worked out the way the published mark schemes do it."""

    marks: int
    available: int
    errors: int = 0
    missing: List[int] = field(default_factory=list)
    extra: List[int] = field(default_factory=list)

    @property
    def full(self) -> bool:
        return self.marks == self.available


def mark_sample(correct: Sequence[int], given: Sequence[int], available: int) -> Award:
    """Mark a list of values against the expected list.

    Cambridge marks a random-number sample on the numbers obtained. Nov 2023
    paper 22 Q3(b)(ii): "B3, (B2 for 1 error/omission), (B1 for 2
    errors/omissions)". One wrong value costs one mark, down to zero.
    """
    want, got = list(correct), list(given)
    missing = [v for v in want if v not in got]
    extra = [v for v in got if v not in want]
    errors = max(len(missing), len(extra))
    if len(got) != len(want):
        errors = max(errors, abs(len(got) - len(want)))
    return Award(marks=max(0, available - errors), available=available,
                 errors=errors, missing=missing, extra=extra)


def mark_value(correct: Any, given: Any, available: int = 1) -> Award:
    ok = given is not None and str(given).strip() == str(correct).strip()
    try:
        ok = ok or (given is not None and int(given) == int(correct))
    except (TypeError, ValueError):
        pass
    return Award(marks=available if ok else 0, available=available, errors=0 if ok else 1)


def mark_count(correct: Sequence[Any], given: Sequence[Any], available: int) -> Award:
    """All of them right scores everything; some of them right scores part."""
    right = sum(1 for a, b in zip(correct, given) if str(a) == str(b))
    if right == len(correct):
        marks = available
    elif right:
        marks = max(1, available - 1)
    else:
        marks = 0
    return Award(marks=marks, available=available, errors=len(correct) - right)


def parse_numbers(text: str) -> List[int]:
    """Read a student's answer, however they separated it."""
    out: List[int] = []
    token = ""
    for ch in str(text):
        if ch.isdigit():
            token += ch
        elif token:
            out.append(int(token))
            token = ""
    if token:
        out.append(int(token))
    return out
