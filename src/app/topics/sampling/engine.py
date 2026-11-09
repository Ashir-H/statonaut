"""Selection from a random number table.

Implements the three examinable methods (simple random, systematic, stratified)
exactly as Cambridge IGCSE Statistics 0479 and O Level Statistics 4040 mark
them, so that every answer the app shows a student is computed, not stored:

* Numbers are read in blocks the same width as the population labels.
* Simple random: reject a number outside the label range, reject a repeat.
* Systematic: the table is used once, for the start only, and the valid start
  range is the first interval. A real member larger than the interval is still
  rejected.
* Stratified: one pass along the table, each number sent to its own group,
  skipping any number whose group is already fully sampled.
* A rejected number is never rounded into range.
"""

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

ACCEPT = "accept"
REJECT = "reject"
SKIP = "skip"

# Reason codes, so the drill can compare a student's choice with the engine's.
R_IN_RANGE = "in range"
R_OUT_OF_RANGE = "out of range"
R_REPEAT = "repeat"
R_GROUP_FULL = "group full"
R_OVER_INTERVAL = "over interval"


# ----------------------------------------------------------------- the table


def digits(row: str) -> str:
    """The table as a bare digit string, however it was spaced when printed."""
    return "".join(ch for ch in str(row) if ch.isdigit())


def in_pairs(row: str) -> str:
    """How Cambridge prints a random number table: digits in pairs."""
    d = digits(row)
    return " ".join(d[i : i + 2] for i in range(0, len(d), 2))


def read_blocks(row: str, width: int) -> List[str]:
    """The table regrouped into the blocks the question actually needs.

    A trailing part-block is dropped: it cannot be read as a label.
    """
    d = digits(row)
    whole = len(d) // width
    return [d[i * width : (i + 1) * width] for i in range(whole)]


def label_width(hi: int) -> int:
    """Labels are written with as many digits as the largest one needs."""
    return max(2, len(str(hi)))


def pad(value: int, width: int) -> str:
    return str(value).zfill(width)


def pad_all(values: Sequence[int], width: int) -> List[str]:
    return [pad(v, width) for v in values]


# ------------------------------------------------------------------- strata


@dataclass
class Stratum:
    name: str
    lo: int
    hi: int

    @property
    def size(self) -> int:
        return self.hi - self.lo + 1

    def contains(self, value: int) -> bool:
        return self.lo <= value <= self.hi

    def label_range(self, width: int) -> str:
        return f"{pad(self.lo, width)}–{pad(self.hi, width)}"


@dataclass
class StratumShare:
    """One row of the sample-size calculation, kept in the form Cambridge marks."""

    name: str
    size: int
    exact: Fraction
    count: int

    @property
    def is_whole(self) -> bool:
        return self.exact.denominator == 1

    def working(self, population: int, sample: int) -> str:
        return f"{self.size}/{population} × {sample} = {self.count}"


def strata_shares(strata: Sequence[Stratum], sample: int) -> List[StratumShare]:
    """Proportional sample size per stratum, with the working line for each."""
    population = sum(s.size for s in strata)
    shares = []
    for s in strata:
        exact = Fraction(s.size * sample, population)
        shares.append(
            StratumShare(
                name=s.name,
                size=s.size,
                exact=exact,
                count=int(exact) if exact.denominator == 1 else round(float(exact)),
            )
        )
    return shares


# -------------------------------------------------------------------- steps


@dataclass
class Step:
    """One block of the table, and what happens to it."""

    index: int
    block: str
    value: int
    action: str
    reason: str
    stratum: Optional[str] = None

    @property
    def taken(self) -> bool:
        return self.action == ACCEPT


@dataclass
class Result:
    method: str
    width: int
    steps: List[Step] = field(default_factory=list)
    sample: List[int] = field(default_factory=list)
    complete: bool = False
    # systematic only
    interval: Optional[int] = None
    start: Optional[int] = None
    # stratified only
    picks: Dict[str, List[int]] = field(default_factory=dict)
    shares: List[StratumShare] = field(default_factory=list)
    population: Optional[int] = None

    @property
    def blocks_used(self) -> int:
        return len(self.steps)

    def labels(self) -> List[str]:
        return pad_all(self.sample, self.width)


# ---------------------------------------------------------- simple random


def simple_random(row: str, lo: int, hi: int, n: int) -> Result:
    width = label_width(hi)
    res = Result(method="simple random", width=width)
    chosen: List[int] = []
    for i, block in enumerate(read_blocks(row, width)):
        value = int(block)
        if value < lo or value > hi:
            res.steps.append(Step(i, block, value, REJECT, R_OUT_OF_RANGE))
        elif value in chosen:
            res.steps.append(Step(i, block, value, REJECT, R_REPEAT))
        else:
            chosen.append(value)
            res.steps.append(Step(i, block, value, ACCEPT, R_IN_RANGE))
            if len(chosen) == n:
                break
    res.sample = chosen
    res.complete = len(chosen) == n
    return res


# ------------------------------------------------------------- systematic


def interval(population: int, n: int) -> int:
    """Sampling interval k. Cambridge takes the whole-number part."""
    return population // n


def systematic(row: str, lo: int, hi: int, n: int) -> Result:
    """The table gives the random start only; the rest is arithmetic.

    The start is read in blocks wide enough for the largest possible start,
    which is the interval - not the width of the population labels. This is
    why a 400-item population with an interval of 50 is read in pairs.
    """
    population = hi - lo + 1
    k = interval(population, n)
    highest_start = lo + k - 1
    width = label_width(highest_start)
    res = Result(method="systematic", width=label_width(hi), interval=k)
    start: Optional[int] = None
    for i, block in enumerate(read_blocks(row, width)):
        value = int(block)
        if lo <= value <= highest_start:
            start = value
            res.steps.append(Step(i, block, value, ACCEPT, R_IN_RANGE))
            break
        if value > hi or value < lo:
            res.steps.append(Step(i, block, value, REJECT, R_OUT_OF_RANGE))
        else:
            # A real member of the population, but it cannot be the start.
            res.steps.append(Step(i, block, value, REJECT, R_OVER_INTERVAL))
    if start is None:
        res.complete = False
        return res
    res.start = start
    res.sample = [start + j * k for j in range(n)]
    res.complete = res.sample[-1] <= hi
    return res


def start_read_width(lo: int, hi: int, n: int) -> int:
    """How wide the blocks are when hunting for a systematic start."""
    return label_width(lo + interval(hi - lo + 1, n) - 1)


# ------------------------------------------------------------- stratified


def stratified(row: str, strata: Sequence[Stratum], n: int) -> Result:
    population = sum(s.size for s in strata)
    lo = min(s.lo for s in strata)
    hi = max(s.hi for s in strata)
    width = label_width(hi)
    shares = strata_shares(strata, n)
    quota = {sh.name: sh.count for sh in shares}
    picks: Dict[str, List[int]] = {s.name: [] for s in strata}

    res = Result(method="stratified", width=width, shares=shares)
    taken: List[int] = []
    for i, block in enumerate(read_blocks(row, width)):
        value = int(block)
        if value < lo or value > hi:
            res.steps.append(Step(i, block, value, REJECT, R_OUT_OF_RANGE))
            continue
        home = next((s for s in strata if s.contains(value)), None)
        if home is None:
            res.steps.append(Step(i, block, value, REJECT, R_OUT_OF_RANGE))
            continue
        if value in taken:
            res.steps.append(Step(i, block, value, REJECT, R_REPEAT, home.name))
            continue
        if len(picks[home.name]) >= quota[home.name]:
            res.steps.append(Step(i, block, value, SKIP, R_GROUP_FULL, home.name))
            continue
        picks[home.name].append(value)
        taken.append(value)
        res.steps.append(Step(i, block, value, ACCEPT, R_IN_RANGE, home.name))
        if sum(len(v) for v in picks.values()) == sum(quota.values()):
            break

    res.picks = picks
    res.sample = taken
    res.complete = sum(len(v) for v in picks.values()) == sum(quota.values())
    res.population = population
    return res
