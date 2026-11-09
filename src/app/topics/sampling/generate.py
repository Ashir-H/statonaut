"""Question generation.

Every generated question is built from a seed, so the same four-digit code
always produces the same question - a teacher can put a code on the board and
every student sees the same table. The engine then solves whatever was built,
so the answer can never drift from the question.

Rows are composed rather than drawn blindly, so that each question is certain
to contain the features worth practising: numbers outside the range, a repeat,
a member that is too large to be a systematic start, a group that fills up
before the table runs out.
"""

import random
from typing import Dict, List, Optional, Sequence

from . import engine
from .engine import Stratum

# --------------------------------------------------------------- scenarios

SIMPLE_CONTEXTS = [
    ("A school has {N} students in Year 10.", "students", "survey about school lunches"),
    ("A library lent {N} books last week.", "books", "check on how many were returned late"),
    ("A factory produced {N} light bulbs in one shift.", "light bulbs", "test of how long they last"),
    ("A clinic has {N} patients on its register.", "patients", "survey about waiting times"),
    ("A delivery depot handled {N} parcels on Monday.", "parcels", "check on delivery times"),
    ("A sports centre has {N} members.", "members", "survey about opening hours"),
    ("An orchard has {N} apple trees.", "trees", "study of this year's yield"),
    ("A hotel has {N} rooms.", "rooms", "inspection of cleaning standards"),
    ("A bus company runs {N} journeys each week.", "journeys", "study of how often buses run late"),
    ("A college entered {N} candidates for an examination.", "candidates", "check on marking accuracy"),
]

STRATIFIED_CONTEXTS = [
    ("A sports club has {N} members.", "members", ["Junior", "Senior", "Veteran"]),
    ("A school has {N} students in the upper school.", "students", ["Year 9", "Year 10", "Year 11"]),
    ("A factory has {N} workers.", "workers", ["Day shift", "Evening shift", "Night shift"]),
    ("A garden centre has {N} plants for sale.", "plants", ["Shrubs", "Trees", "Herbs"]),
    ("A bookshop has {N} books in stock.", "books", ["Fiction", "Non-fiction", "Children's"]),
    ("A farm has {N} animals.", "animals", ["Sheep", "Goats", "Cattle"]),
    ("A music school has {N} pupils.", "pupils", ["Strings", "Woodwind", "Percussion"]),
    ("A call centre employs {N} staff.", "staff", ["Sales", "Support", "Accounts"]),
]


def _digits(rng: random.Random, count: int) -> str:
    return "".join(str(rng.randrange(10)) for _ in range(count))


MIN_DIGITS = 26   # thirteen printed pairs, the length Cambridge tends to use


def _row_from_blocks(rng: random.Random, blocks: Sequence[str], width: int,
                     spare: int = 3) -> str:
    """Pad a planned sequence of blocks out to a full printed row.

    Filler goes only on the end, after the question has been answered, so it
    can never change the sample.
    """
    out = list(blocks)
    least = max(len(out) + spare, -(-MIN_DIGITS // width))
    while len(out) < least:
        out.append(_digits(rng, width))
    digits = "".join(out)
    if len(digits) % 2:
        digits += str(rng.randrange(10))
    return engine.in_pairs(digits)


def _label(value: int, width: int) -> str:
    return str(value).zfill(width)


# ----------------------------------------------------------- simple random


def simple_random_question(seed: int) -> Dict:
    rng = random.Random(seed * 7 + 11)
    setting, noun, purpose = rng.choice(SIMPLE_CONTEXTS)
    three_digit = rng.random() < 0.45
    zero_based = three_digit and rng.random() < 0.35

    if three_digit:
        population = rng.choice([120, 150, 180, 200, 240, 250, 300, 320, 350, 400, 450, 500])
        width = 3
    else:
        population = rng.choice([30, 36, 40, 45, 48, 50, 54, 60, 64, 70, 75, 80])
        width = 2
    lo = 0 if zero_based else 1
    hi = population - 1 if zero_based else population
    n = rng.choice([4, 5, 6]) if three_digit else rng.choice([5, 6, 7])

    # Plan the row. Everything that is rejected is placed before the last
    # member, so the student actually meets it: the engine stops reading the
    # moment the sample is full.
    members = rng.sample(range(lo, hi + 1), n)
    ceiling = 10 ** width - 1
    plan: List[str] = [_label(v, width) for v in members]

    for _ in range(rng.randrange(2, 4)):
        plan.insert(rng.randrange(1, len(plan)), _label(rng.randrange(hi + 1, ceiling), width))
    repeated = members[rng.randrange(0, n - 1)]
    first_at = plan.index(_label(repeated, width))
    plan.insert(rng.randrange(first_at + 1, len(plan)), _label(repeated, width))

    row = _row_from_blocks(rng, plan, width)
    result = engine.simple_random(row, lo, hi, n)
    assert result.complete and result.sample == members, (result.sample, members)
    return {
        "kind": "simple",
        "seed": seed,
        "setting": setting.format(N=population),
        "noun": noun,
        "purpose": purpose,
        "lo": lo,
        "hi": hi,
        "population": population,
        "n": n,
        "row": row,
        "width": width,
        "marks": 2 if n <= 6 else 3,
        "result": result,
    }


# -------------------------------------------------------------- systematic


def systematic_question(seed: int) -> Dict:
    rng = random.Random(seed * 13 + 29)
    setting, noun, purpose = rng.choice(SIMPLE_CONTEXTS)
    n = rng.choice([5, 6, 8, 10])
    k = rng.choice([10, 12, 15, 20, 25, 40, 50])
    population = n * k
    three_digit = population > 99
    zero_based = three_digit and rng.random() < 0.4
    lo = 0 if zero_based else 1
    hi = population - 1 if zero_based else population

    start_width = engine.start_read_width(lo, hi, n)
    highest_start = lo + k - 1
    ceiling = 10 ** start_width - 1
    start = rng.randrange(lo, highest_start + 1)

    plan: List[str] = []
    # A real member of the population that is too large to be the start.
    if highest_start + 1 <= min(hi, ceiling):
        plan.append(_label(rng.randrange(highest_start + 1, min(hi, ceiling) + 1), start_width))
    # A number outside the population altogether, where the width allows one.
    if hi < ceiling:
        plan.append(_label(rng.randrange(hi + 1, ceiling + 1), start_width))
    rng.shuffle(plan)
    plan.append(_label(start, start_width))

    row = _row_from_blocks(rng, plan, start_width, spare=6)
    result = engine.systematic(row, lo, hi, n)
    assert result.complete and result.start == start, (result.start, start)
    return {
        "kind": "systematic",
        "seed": seed,
        "setting": setting.format(N=population),
        "noun": noun,
        "purpose": purpose,
        "lo": lo,
        "hi": hi,
        "population": population,
        "n": n,
        "row": row,
        "width": engine.label_width(hi),
        "start_width": start_width,
        "marks": 3,
        "result": result,
    }


# -------------------------------------------------------------- stratified


def _split(rng: random.Random, total: int, parts: int) -> List[int]:
    while True:
        cuts = sorted(rng.sample(range(1, total), parts - 1))
        sizes = [b - a for a, b in zip([0] + cuts, cuts + [total])]
        if all(s >= 1 for s in sizes) and len(set(sizes)) > 1:
            return sizes


def stratified_question(seed: int) -> Dict:
    rng = random.Random(seed * 17 + 43)
    setting, noun, groups = rng.choice(STRATIFIED_CONTEXTS)
    n = rng.choice([5, 6, 7, 8])
    per = rng.choice([6, 8, 10, 12, 15, 20, 25, 30])
    shares = _split(rng, n, 3)
    sizes = [s * per for s in shares]
    population = sum(sizes)
    width = engine.label_width(population)
    ceiling = 10 ** width - 1

    strata: List[Stratum] = []
    cursor = 1
    for name, size in zip(groups, sizes):
        strata.append(Stratum(name, cursor, cursor + size - 1))
        cursor += size

    # Plan a row that fills every group, and make sure the row also contains
    # a repeat, a number outside the range, and a number whose group has
    # already closed - the three things this method is tested on.
    wanted = {s.name: rng.sample(range(s.lo, s.hi + 1), q)
              for s, q in zip(strata, shares)}
    by_name = {s.name: s for s in strata}
    order = [(s.name, v) for s in strata for v in wanted[s.name]]
    rng.shuffle(order)

    plan: List[str] = []
    placed = {s.name: 0 for s in strata}
    done_repeat = done_outside = done_full = False
    for idx, (name, value) in enumerate(order):
        plan.append(_label(value, width))
        placed[name] += 1
        if not done_repeat and idx == 0:
            plan.append(_label(value, width))
            done_repeat = True
        if not done_outside and idx == 1 and population < ceiling:
            plan.append(_label(rng.randrange(population + 1, ceiling + 1), width))
            done_outside = True
        if not done_full and placed[name] == len(wanted[name]) and idx < len(order) - 1:
            home = by_name[name]
            spare = [v for v in range(home.lo, home.hi + 1) if v not in wanted[name]]
            if spare:
                plan.append(_label(rng.choice(spare), width))
                done_full = True

    row = _row_from_blocks(rng, plan, width)
    result = engine.stratified(row, strata, n)
    assert result.complete, result.picks
    return {
        "kind": "stratified",
        "seed": seed,
        "setting": setting.format(N=population),
        "noun": noun,
        "lo": 1,
        "hi": population,
        "population": population,
        "n": n,
        "row": row,
        "width": width,
        "strata": strata,
        "marks": 3 if n >= 6 else 2,
        "size_marks": 2,
        "result": result,
    }


# ------------------------------------------- interval from two known members


def interval_question(seed: int) -> Dict:
    """Cambridge's 'smallest possible sample size' question.

    Nov 2023 paper 22 Q3(a): two members of a systematic sample are given,
    M1 for the difference, A1 for population divided by the difference. The
    smallest possible size is asked for, because the two members given are
    not stated to be consecutive.
    """
    rng = random.Random(seed * 19 + 7)
    setting, noun, purpose = rng.choice(SIMPLE_CONTEXTS)
    n = rng.choice([8, 10, 12, 15, 16, 20, 24, 25])
    k = rng.choice([8, 10, 12, 15, 20, 25, 30, 40, 50, 60])
    population = n * k
    first = rng.randrange(1, k + 1)
    gap = rng.choice([g for g in (1, 2, 3, 4) if n % g == 0 and g < n])
    a = first + rng.randrange(0, max(1, n - gap)) * k
    b = a + gap * k
    return {
        "kind": "interval",
        "seed": seed,
        "setting": setting.format(N=population),
        "noun": noun,
        "population": population,
        "a": a,
        "b": b,
        "gap": gap,
        "difference": b - a,
        "answer": population // (b - a),
        "interval": b - a,
        "marks": 2,
    }


# --------------------------------------------- representative or not (1.4)


def representative_question(seed: int) -> Dict:
    """Syllabus 1.4: show whether or not a given sample is representative."""
    rng = random.Random(seed * 23 + 5)
    setting, noun, groups = rng.choice(STRATIFIED_CONTEXTS)
    n = rng.choice([20, 24, 25, 30, 40, 50])
    per = rng.choice([4, 5, 6, 8, 10])
    shares = _split(rng, n, 3)
    sizes = [s * per for s in shares]
    population = sum(sizes)
    fair = rng.random() < 0.4
    if fair:
        observed = list(shares)
    else:
        observed = list(shares)
        i = observed.index(max(observed))
        j = rng.choice([x for x in range(3) if x != i])
        shift = rng.randrange(2, observed[i]) if observed[i] > 2 else 1
        observed[i] -= shift
        observed[j] += shift
    return {
        "kind": "representative",
        "seed": seed,
        "setting": setting.format(N=population),
        "noun": noun,
        "groups": list(groups),
        "sizes": sizes,
        "population": population,
        "n": n,
        "expected": list(shares),
        "observed": observed,
        "fair": observed == list(shares),
        "marks": 3,
    }


BUILDERS = {
    "simple": simple_random_question,
    "systematic": systematic_question,
    "stratified": stratified_question,
    "interval": interval_question,
    "representative": representative_question,
}


def build(kind: str, seed: int) -> Dict:
    return BUILDERS[kind](seed)


def new_seed(rng: Optional[random.Random] = None) -> int:
    r = rng or random
    return r.randrange(1000, 10000)
