"""The situations for the page on selecting a measure.

The situations live in `content/central-tendency/choosing.toml` so that the
wording of a reason can be corrected without touching code. This module reads
that file, pairs each situation with the statements offered against it, and can
report every way in which the file contradicts itself, which is what the tests
use.

Nothing here imports Streamlit, so the whole module can be exercised directly.
"""

import random
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from app.core.library import ContentError

from . import content, engine

MEASURES = ("mode", "median", "mean")

NAMES = {"mode": "The mode", "median": "The median", "mean": "The mean"}


@dataclass(frozen=True)
class Situation:
    """One set of data, the measure that best describes it, and why."""

    key: str
    setting: str
    label: str
    answer: str
    reason: str
    distractors: Tuple[str, ...]
    values: Tuple[int, ...] = ()
    categories: Tuple[str, ...] = ()
    frequencies: Tuple[int, ...] = ()

    @property
    def numerical(self) -> bool:
        return bool(self.values)

    def statements(self, seed: int) -> List[str]:
        """The reason and the statements offered against it, in a fixed order.

        Shuffled from the seed rather than at random, so that the same code
        gives the same question to every student.
        """
        out = [self.reason, *self.distractors]
        random.Random(seed * 31 + 7).shuffle(out)
        return out


def _situation(raw: Dict) -> Situation:
    return Situation(
        key=str(raw.get("key", "")),
        setting=str(raw.get("setting", "")),
        label=str(raw.get("label", "")),
        answer=str(raw.get("answer", "")),
        reason=str(raw.get("reason", "")),
        distractors=tuple(raw.get("distractors", ())),
        values=tuple(int(v) for v in raw.get("values", ())),
        categories=tuple(str(c) for c in raw.get("categories", ())),
        frequencies=tuple(int(f) for f in raw.get("frequencies", ())),
    )


def situations() -> List[Situation]:
    data = content.choosing_data()
    found = data.get("situation")
    if not found:
        raise ContentError(
            "choosing.toml has no [[situation]] entries, so the page has nothing "
            "to ask.")
    return [_situation(raw) for raw in found]


def pick(seed: int) -> Situation:
    """One situation, chosen by the seed so a code always gives the same one."""
    bank = situations()
    return bank[seed % len(bank)]


def complaints() -> List[str]:
    """Every way the file contradicts itself. Used by the tests."""
    trouble: List[str] = []
    try:
        bank = situations()
    except ContentError as exc:
        return [str(exc)]

    seen = set()
    for item in bank:
        where = f"choosing.toml [{item.key or '?'}]"
        if not item.key:
            trouble.append(f"{where}: no key")
        elif item.key in seen:
            trouble.append(f"{where}: the key is used twice")
        seen.add(item.key)
        for field in ("setting", "label", "reason"):
            if not getattr(item, field):
                trouble.append(f"{where}: {field} is empty")
        if item.answer not in MEASURES:
            trouble.append(f"{where}: the answer is {item.answer!r}, not one of "
                           f"{', '.join(MEASURES)}")
        if len(item.distractors) != 3:
            trouble.append(f"{where}: {len(item.distractors)} statements offered "
                           f"against the reason, expected 3")
        if item.reason in item.distractors:
            trouble.append(f"{where}: the reason is also offered as a distractor")
        if len(set(item.distractors)) != len(item.distractors):
            trouble.append(f"{where}: a distractor is repeated")

        if item.numerical and item.categories:
            trouble.append(f"{where}: both values and categories are given")
        elif item.numerical:
            far = engine.extreme_values(item.values)
            if item.answer == "median" and not far:
                trouble.append(f"{where}: the median is offered, but no value lies "
                               f"far enough from the rest to pull the mean")
            if item.answer == "mean" and far:
                trouble.append(f"{where}: the mean is offered, but {far} lies far "
                               f"from the rest and would pull it")
            if item.answer == "mode" and engine.mode_of(item.values) is None:
                trouble.append(f"{where}: the mode is offered, but no value occurs "
                               f"more often than the others")
        elif item.categories:
            if len(item.categories) != len(item.frequencies):
                trouble.append(f"{where}: {len(item.categories)} categories and "
                               f"{len(item.frequencies)} frequencies")
            elif item.answer != "mode":
                trouble.append(f"{where}: the data is not numerical, so only the "
                               f"mode can be offered, not {item.answer}")
            else:
                highest = max(item.frequencies)
                if item.frequencies.count(highest) != 1:
                    trouble.append(f"{where}: two categories share the highest "
                                   f"frequency, which no mark scheme covers")
        else:
            trouble.append(f"{where}: neither values nor categories are given")
    return trouble
