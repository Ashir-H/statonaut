"""The three measures, and the steps a mark scheme wants to see on the way.

Nothing here draws anything and there is no Streamlit import, so the whole
module can be exercised by the tests on any interpreter.

Three conventions come straight from the published mark schemes, and each one
is easy to get wrong:

* An ungrouped median is marked on the position (n+1)/2. The formula is never
  printed in a question; ordering the data and counting to that position is
  itself what earns the mark, which is why `solve_list` reports the ordered
  values and the position separately rather than only the answer.
* A frequency table is marked on the f x values being visible and on the
  division by the sum of the frequencies. Two mark schemes cap a bare answer
  at one mark, so the table solution exposes the column and the two totals as
  separate steps.
* The median of a table comes from the running total, never from the x column.
  `median_rows` says which row the middle value falls in, so a page can show
  the counting rather than assert the answer.

The mode is deliberately strict. In the whole 4040 archive no question has a
tied highest frequency, and no mark scheme anywhere says what to do with one,
so a tie reports no mode rather than inventing a convention the papers have
never tested. The generator refuses to build such a question in the first
place.
"""

import math
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional, Sequence, Tuple

# ------------------------------------------------------------------- numbers


def rounded(value: float, figures: int = 3) -> float:
    """Round to significant figures, half upwards, the way a student would.

    Decimal rather than round(): 77/40 is exactly 1.925 and the mark scheme
    gives 1.93, but the nearest float is a shade under, so round() would give
    1.92 and the drill would mark a correct answer wrong.
    """
    if value == 0:
        return 0.0
    number = Decimal(str(value))
    places = figures - 1 - number.adjusted()
    step = Decimal(1).scaleb(-places)
    return float(number.quantize(step, rounding=ROUND_HALF_UP))


def shown(value: float, figures: int = 3) -> str:
    """A number written the way a student would write it on the paper."""
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{rounded(value, figures):g}"


def agrees(exact: float, given: Optional[float], figures: int = 3) -> bool:
    """Whether an answer earns the mark.

    The exact value is right, and so is any value that agrees with it to the
    required number of significant figures: 10.7 and 10.67 both earn the mark
    for 480 divided by 45, and 10.6 does not.
    """
    if given is None:
        return False
    if abs(given - exact) < 1e-9:
        return True
    return abs(rounded(given, figures) - rounded(exact, figures)) < 1e-9


# --------------------------------------------------------------- a plain list


def position(n: int) -> float:
    """Where the median sits: the (n+1)/2 th value."""
    return (n + 1) / 2


def median_of(values: Sequence[int]) -> float:
    data = sorted(values)
    n = len(data)
    if n == 0:
        raise ValueError("no values")
    middle = n // 2
    if n % 2:
        return float(data[middle])
    return (data[middle - 1] + data[middle]) / 2


def counts(values: Sequence[int]) -> List[Tuple[int, int]]:
    """Every distinct value with how often it occurs, in order of value."""
    return [(v, list(values).count(v)) for v in sorted(set(values))]


def mode_of(values: Sequence[int]) -> Optional[int]:
    """The mode, or nothing at all when the highest frequency is shared."""
    tally = counts(values)
    if not tally:
        return None
    most = max(f for _, f in tally)
    winners = [v for v, f in tally if f == most]
    if len(winners) != 1:
        return None
    if most == 1 and len(tally) > 1:
        return None
    return winners[0]


@dataclass(frozen=True)
class ListAnswers:
    """Everything a question about a plain list can ask for."""

    values: Tuple[int, ...]       # as the question prints them, unordered
    ordered: Tuple[int, ...]      # ordering these is a mark in its own right
    n: int
    position: float
    mode: Optional[int]
    median: float
    mean: float                   # exact; round only when showing it
    total: int
    spread: int                   # the range, which is not a measure of central tendency

    @property
    def middle_values(self) -> Tuple[int, ...]:
        """The one or two values the position lands on."""
        low = math.floor(self.position) - 1
        high = math.ceil(self.position) - 1
        if low == high:
            return (self.ordered[low],)
        return (self.ordered[low], self.ordered[high])


def solve_list(values: Sequence[int]) -> ListAnswers:
    data = list(values)
    n = len(data)
    return ListAnswers(
        values=tuple(data),
        ordered=tuple(sorted(data)),
        n=n,
        position=position(n),
        mode=mode_of(data),
        median=median_of(data),
        mean=sum(data) / n,
        total=sum(data),
        spread=max(data) - min(data),
    )


# --------------------------------------------------- an ungrouped frequency table


@dataclass(frozen=True)
class Row:
    x: int
    f: int

    @property
    def fx(self) -> int:
        return self.x * self.f


def running_totals(rows: Sequence[Row]) -> Tuple[int, ...]:
    out: List[int] = []
    so_far = 0
    for row in rows:
        so_far += row.f
        out.append(so_far)
    return tuple(out)


def expand(rows: Sequence[Row]) -> List[int]:
    """The table written back out as the list it stands for."""
    out: List[int] = []
    for row in rows:
        out.extend([row.x] * row.f)
    return out


def median_rows(rows: Sequence[Row]) -> Tuple[int, ...]:
    """Which row or rows the middle value falls in, found by counting down the
    running total. One row for an odd total, one or two for an even one."""
    running = running_totals(rows)
    n = running[-1] if running else 0
    where = position(n)
    wanted = sorted({math.floor(where), math.ceil(where)})
    found: List[int] = []
    for place in wanted:
        for index, cumulative in enumerate(running):
            if cumulative >= place:
                if index not in found:
                    found.append(index)
                break
    return tuple(found)


@dataclass(frozen=True)
class TableAnswers:
    rows: Tuple[Row, ...]
    sigma_f: int
    sigma_fx: int
    running: Tuple[int, ...]
    position: float
    mode: Optional[int]
    median: float
    mean: float                   # exact; round only when showing it

    @property
    def products(self) -> Tuple[int, ...]:
        return tuple(row.fx for row in self.rows)

    @property
    def median_rows(self) -> Tuple[int, ...]:
        return median_rows(self.rows)


def solve_table(rows: Sequence[Row]) -> TableAnswers:
    table = tuple(rows)
    sigma_f = sum(row.f for row in table)
    sigma_fx = sum(row.fx for row in table)
    if sigma_f == 0:
        raise ValueError("the frequencies add to nothing")
    most = max(row.f for row in table)
    winners = [row.x for row in table if row.f == most]
    return TableAnswers(
        rows=table,
        sigma_f=sigma_f,
        sigma_fx=sigma_fx,
        running=running_totals(table),
        position=position(sigma_f),
        mode=winners[0] if len(winners) == 1 else None,
        median=median_of(expand(table)),
        mean=sigma_fx / sigma_f,
    )
