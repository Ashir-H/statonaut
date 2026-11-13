"""Question generation for the three measures.

Every question is built from a seed, so the same four-digit code always gives
the same question and a teacher can put one code on the board for the class.
The engine then solves whatever was built, so a printed answer can never drift
away from the question it belongs to.

Data is composed rather than drawn blindly, for one reason above all: the
highest frequency must belong to a single value. No question in the 4040
archive has a tied mode and no mark scheme says how to mark one, so a
generated question that produced a tie would be unmarkable. Every builder
checks the engine's own verdict before handing a question back, and the tests
sweep thousands of seeds to confirm it never slips.
"""

import random
from typing import Dict, List, Optional, Sequence, Tuple

from . import engine
from .engine import Row

# ---------------------------------------------------------------- scenarios

LIST_CONTEXTS: Sequence[Tuple[str, str, str]] = [
    ("{n} students were asked how many books they had borrowed from the library "
     "last month.", "Books borrowed", "students"),
    ("A netball team played {n} matches. The number of goals scored in each match "
     "was recorded.", "Goals scored", "matches"),
    ("{n} households were asked how many cars they own.", "Cars owned", "households"),
    ("{n} pupils were asked how many pets they keep at home.", "Pets kept", "pupils"),
    ("A shop was open for {n} days. The number of complaints received each day was "
     "recorded.", "Complaints", "days"),
    ("{n} candidates sat a short test marked out of 12.", "Marks", "candidates"),
    ("{n} members of a cycling club recorded the number of rides they made in one "
     "week.", "Rides", "members"),
    ("A bus was late on {n} mornings. The number of minutes late was recorded each "
     "time.", "Minutes late", "mornings"),
]

TABLE_CONTEXTS: Sequence[Tuple[str, str, str]] = [
    ("{n} students were asked how many pets they keep at home.", "Pets", "Students"),
    ("A football team played {n} matches. The number of goals scored in each match "
     "is shown in the table.", "Goals", "Matches"),
    ("{n} students were asked how many online courses they had completed.",
     "Courses", "Students"),
    ("{n} customers were asked how many items they had bought.", "Items", "Customers"),
    ("The number of days absent was recorded for each of {n} students.",
     "Days absent", "Students"),
    ("{n} families were asked how many children live at home.", "Children", "Families"),
    ("A machine was checked on {n} days and the number of faults was recorded.",
     "Faults", "Days"),
]


# ------------------------------------------------------------- a plain list


def _list_values(rng: random.Random, n: int) -> List[int]:
    """A list with one outright mode, printed out of order.

    The mode is planted first and everything else is kept below its count, then
    the engine is asked whether the result really has a single mode. Anything
    that does not is thrown away rather than patched, so a tie can never reach
    a student.
    """
    for _ in range(300):
        repeats = rng.choice([3, 3, 4])
        if repeats >= n:
            continue
        mode_value = rng.randrange(1, 13)
        values = [mode_value] * repeats
        pool = [v for v in range(1, 14) if v != mode_value]
        rng.shuffle(pool)
        while len(values) < n and pool:
            value = pool.pop()
            times = min(rng.choice([1, 1, 1, 2]), repeats - 1, n - len(values))
            values.extend([value] * times)
        if len(values) != n:
            continue
        rng.shuffle(values)
        # A list that happens to arrive in order would hand over the ordering
        # mark for nothing, so it is thrown back and shuffled again.
        if (engine.mode_of(values) == mode_value
                and max(values) > min(values)
                and list(values) != sorted(values)):
            return values
    raise RuntimeError("could not compose a list with a single mode")


def list_question(seed: int) -> Dict:
    rng = random.Random(seed * 13 + 5)
    setting, label, noun = rng.choice(LIST_CONTEXTS)
    n = rng.choice([7, 8, 9, 9, 10, 11])
    values = _list_values(rng, n)
    return {
        "kind": "list",
        "seed": seed,
        "setting": setting.format(n=n),
        "label": label,
        "noun": noun,
        "values": values,
    }


# --------------------------------------------- an ungrouped frequency table


def _table_rows(rng: random.Random) -> List[Row]:
    """Rows whose highest frequency belongs to exactly one value.

    The peak is lifted above every other frequency rather than hoped for, and
    the engine still has the last word.
    """
    for _ in range(300):
        count = rng.choice([4, 5, 5, 6])
        if rng.random() < 0.3:
            xs = sorted(rng.sample(range(2, 20), count))
        else:
            start = rng.choice([0, 0, 1])
            xs = list(range(start, start + count))
        fs = [rng.randrange(2, 12) for _ in xs]
        peak = rng.randrange(count)
        fs[peak] = max(fs) + rng.choice([1, 2, 3])
        rows = [Row(x, f) for x, f in zip(xs, fs)]
        if not 25 <= sum(fs) <= 60:
            continue
        if engine.solve_table(rows).mode is None:
            continue
        return rows
    raise RuntimeError("could not compose a table with a single mode")


def table_question(seed: int) -> Dict:
    rng = random.Random(seed * 29 + 17)
    setting, x_label, f_label = rng.choice(TABLE_CONTEXTS)
    rows = _table_rows(rng)
    return {
        "kind": "table",
        "seed": seed,
        "setting": setting.format(n=sum(row.f for row in rows)),
        "x_label": x_label,
        "f_label": f_label,
        "rows": [(row.x, row.f) for row in rows],
    }


# ------------------------------------------------- an alteration to the data

CHANGE_CONTEXTS: Sequence[Tuple[str, str]] = [
    ("The number of books borrowed by each of {n} students was recorded.",
     "Books borrowed"),
    ("A shop recorded the number of complaints received on each of {n} days.",
     "Complaints"),
    ("{n} members of a club recorded the number of events they attended.",
     "Events attended"),
    ("The number of goals scored in each of {n} matches was recorded.",
     "Goals scored"),
    ("{n} candidates sat a short test marked out of twelve.", "Marks"),
]


def _described_change(rng: random.Random, values: List[int]):
    """One alteration, described in words, with the altered list beside it.

    An alteration is only offered if a single mode survives it. Where the
    highest frequency becomes shared, no verdict about the mode can be stated,
    and no mark scheme covers that case.
    """
    answers = engine.solve_list(values)
    kinds = ["add", "add", "remove", "shift", "scale", "unknown"]
    rng.shuffle(kinds)
    for kind in kinds:
        if kind == "add":
            # A value chosen to make the verdicts worth thinking about: equal
            # to the mean leaves the mean alone, above everything raises all
            # three, equal to the mode leaves the mode alone.
            candidates = [int(answers.mean)] if answers.mean == int(answers.mean) else []
            candidates += [max(values) + rng.randint(4, 20), answers.mode,
                           int(answers.median)]
            value = rng.choice([c for c in candidates if c >= 0])
            after = values + [value]
            description = f"A further value of {value} is recorded."
        elif kind == "remove":
            value = rng.choice(sorted(set(values)))
            after = list(values)
            after.remove(value)
            description = f"One value of {value} is removed."
        elif kind == "shift":
            step = rng.choice([2, 3, 5, 10])
            if rng.random() < 0.5 and min(values) > step:
                after = [v - step for v in values]
                description = f"Every value is decreased by {step}."
            else:
                after = [v + step for v in values]
                description = f"Every value is increased by {step}."
        elif kind == "scale":
            factor = rng.choice([2, 3])
            after = [v * factor for v in values]
            description = f"Every value is multiplied by {factor}."
        else:
            return ("A further value is recorded, but its size is not stated.",
                    [], False)
        if len(after) < 3 or engine.mode_of(after) is None:
            continue
        return description, after, True
    return ("A further value is recorded, but its size is not stated.", [], False)


def change_question(seed: int) -> Dict:
    rng = random.Random(seed * 37 + 3)
    setting, label = rng.choice(CHANGE_CONTEXTS)
    values = _list_values(rng, rng.choice([7, 8, 9]))
    description, after, told = _described_change(rng, values)
    return {
        "kind": "change",
        "seed": seed,
        "setting": setting.format(n=len(values)),
        "label": label,
        "values": values,
        "change": description,
        "after": after,
        "told": told,
    }


def verdicts(question: Dict) -> Dict[str, str]:
    """What the alteration does to each measure, or that it cannot be said."""
    if not question["told"]:
        return engine.unknown_effect()
    return engine.effect(question["values"], question["after"])


# ----------------------------------- questions that give a measure already

BACKWARDS = ("total", "missing", "frequency", "combined")

# The relationship a question of each shape turns on, with three that look
# like it. The first distractor for a combined mean is the error the papers
# punish most often: averaging the two means as though the groups were the
# same size.
RELATIONS: Dict[str, Tuple[str, List[str]]] = {
    "total": (
        r"\text{total} = \text{mean} \times n",
        [r"\text{total} = \frac{\text{mean}}{n}",
         r"\text{total} = \text{mean} + n",
         r"n = \text{mean} \times \text{total}"],
    ),
    "missing": (
        r"x = \text{mean} \times n - \Sigma(\text{the values given})",
        [r"x = \text{mean} \times n + \Sigma(\text{the values given})",
         r"x = \frac{\Sigma(\text{the values given})}{n}",
         r"x = \text{mean} - \Sigma(\text{the values given})"],
    ),
    "frequency": (
        r"\Sigma fx = \text{mean} \times \Sigma f",
        [r"\Sigma fx = \text{mean} \times \text{number of rows}",
         r"k = \text{mean} \times \Sigma f",
         r"\Sigma f = \text{mean} \times \Sigma fx"],
    ),
    "combined": (
        r"\text{mean} = \frac{n_1 m_1 + n_2 m_2}{n_1 + n_2}",
        [r"\text{mean} = \frac{m_1 + m_2}{2}",
         r"\text{mean} = \frac{n_1 + n_2}{m_1 + m_2}",
         r"\text{mean} = n_1 m_1 + n_2 m_2"],
    ),
}

PARCELS = [("parcels", "kg"), ("sacks of flour", "kg"), ("crates", "kg"),
           ("bottles", "litres")]


def _tenths(value: float) -> bool:
    """Whether a figure can be written with at most one decimal place."""
    return abs(value * 10 - round(value * 10)) < 1e-9


def _total_question(rng: random.Random) -> Dict:
    count = rng.choice([8, 10, 12, 15, 20])
    mean = rng.choice([1.5, 2.4, 3.5, 4.2, 5.6, 6.5])
    noun, unit = rng.choice(PARCELS)
    return {
        "setting": f"The mean mass of {count} {noun} is {mean} {unit}.",
        "task": f"Find the total mass of the {noun}.",
        "answer": engine.total_from_mean(mean, count),
        "unit": unit,
    }


def _missing_question(rng: random.Random) -> Dict:
    for _ in range(200):
        count = rng.choice([5, 6, 7])
        mean = rng.randint(10, 18)
        known = [rng.randint(8, 20) for _ in range(count - 1)]
        missing = engine.missing_value(known, mean, count)
        if not 1 <= missing <= 25 or missing in (0,):
            continue
        return {
            "setting": f"{count} candidates sat a test. The marks of "
                       f"{count - 1} of them were "
                       f"{', '.join(str(v) for v in known)}. The mean mark of all "
                       f"{count} candidates was {mean}.",
            "task": "Find the mark of the remaining candidate.",
            "answer": float(missing),
            "unit": "",
        }
    raise RuntimeError("could not compose a missing-value question")


def _frequency_question(rng: random.Random) -> Dict:
    for _ in range(300):
        width = rng.choice([4, 5])
        xs = list(range(width))
        hidden = rng.randrange(width)
        k = rng.randint(3, 14)
        fs = [rng.randint(2, 10) for _ in xs]
        fs[hidden] = k
        rows = [Row(x, f) for x, f in zip(xs, fs)]
        whole = engine.solve_table(rows)
        if not _tenths(whole.mean) or whole.mean == xs[hidden]:
            continue
        known = [row for index, row in enumerate(rows) if index != hidden]
        recovered = engine.missing_frequency(known, xs[hidden], whole.mean)
        if abs(recovered - k) > 1e-6:
            continue
        return {
            "setting": "The table shows the number of goals scored in a number of "
                       "matches. One frequency is not given.",
            "task": f"The mean number of goals is {engine.shown(whole.mean)}. "
                    f"Find the value of k.",
            "answer": float(k),
            "unit": "",
            "rows": [(row.x, row.f) for row in rows],
            "hidden": hidden,
        }
    raise RuntimeError("could not compose a missing-frequency question")


def _combined_question(rng: random.Random) -> Dict:
    for _ in range(300):
        first, second = rng.randint(10, 25), rng.randint(10, 25)
        first_mean, second_mean = rng.randint(50, 80), rng.randint(50, 80)
        if first_mean == second_mean:
            continue
        whole = engine.combined_mean(first, first_mean, second, second_mean)
        if not _tenths(whole):
            continue
        return {
            "setting": f"One group of {first} students has a mean mark of "
                       f"{first_mean}. A second group of {second} students has a "
                       f"mean mark of {second_mean}.",
            "task": "Find the mean mark of all the students together.",
            "answer": whole,
            "unit": "",
        }
    raise RuntimeError("could not compose a combined-mean question")


_BACKWARDS_BUILDERS = {
    "total": _total_question,
    "missing": _missing_question,
    "frequency": _frequency_question,
    "combined": _combined_question,
}


def backwards_question(seed: int) -> Dict:
    rng = random.Random(seed * 41 + 13)
    shape = rng.choice(BACKWARDS)
    built = _BACKWARDS_BUILDERS[shape](rng)
    right, wrong = RELATIONS[shape]
    options = [right, *wrong]
    random.Random(seed * 17 + 5).shuffle(options)
    built.update({"kind": "backwards", "shape": shape, "seed": seed,
                  "relation": right, "options": options})
    return built


# ------------------------------------------------------------------ the gate

BUILDERS = {
    "list": list_question,
    "table": table_question,
    "change": change_question,
    "backwards": backwards_question,
}


def build(kind: str, seed: int) -> Dict:
    return BUILDERS[kind](seed)


def rows_of(question: Dict) -> List[Row]:
    return [Row(x, f) for x, f in question["rows"]]


def solve(question: Dict):
    """Solve whichever kind of question this is."""
    if question["kind"] == "list":
        return engine.solve_list(question["values"])
    return engine.solve_table(rows_of(question))


def signature(question: Dict) -> str:
    """Identifies the question, so a remembered mark belongs to this one only."""
    return f"{question['kind']}:{question['seed']}"


def new_seed(rng: Optional[random.Random] = None) -> int:
    source = rng or random
    return source.randrange(1000, 10000)
