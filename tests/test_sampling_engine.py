"""Every answer here is one already verified in the class materials.

Sources, by project doc:
  claude/unit1-data-and-its-collection.md   worked examples and Part 4 practice
  claude/worksheet-random-number-tables.md  worksheet questions 1-5
  claude/ca1-retake.md                      retake questions 2-4
  claude/cambridge-source-evidence-topic1.md  0479 2027 specimen paper 2 Q2(b)
  claude/4040-past-paper-index.md           4040 Nov 2023 p22 Q3, Nov 2024 p22 Q8

If a change to the engine breaks one of these, the engine is wrong, not the test.
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from app.core.marks import mark_sample
from app.topics.sampling.engine import (
    Stratum, simple_random, systematic, stratified, strata_shares,
    interval, start_read_width, read_blocks, in_pairs,
)

checks = []


def check(name, got, want):
    ok = got == want
    checks.append((ok, name, got, want))
    return ok


# --- Unit 1 deck, worked examples -------------------------------------------
ROW1 = "68 05 41 05 89 23 60 17 74 36 91 08 52 66 30 47"
ROW2 = "74 21 09 63 30 86 12 45 07 58 93 26 51 04 77 39"
ROW3 = "79 06 41 18 36 06 29 02 15 88 53 67 24 90 11 44"
ROW4 = "97 38 69 43 06 89 13 44 91 40 65 52 05 88 03 34"

check("deck simple random, 60 students, n=5",
      simple_random(ROW1, 1, 60, 5).sample, [5, 41, 23, 60, 17])

r = systematic(ROW2, 1, 60, 6)
check("deck systematic, 60 students, n=6, interval", r.interval, 10)
check("deck systematic, start", r.start, 9)
check("deck systematic, sample", r.sample, [9, 19, 29, 39, 49, 59])

club = [Stratum("Junior", 1, 36), Stratum("Senior", 37, 66), Stratum("Veteran", 67, 90)]
check("deck stratified, club of 90, n=15, sizes",
      [s.count for s in strata_shares(club, 15)], [6, 5, 4])
check("deck stratified, juniors drawn from row 3",
      stratified(ROW3, club, 15).picks["Junior"], [6, 18, 36, 29, 2, 15])

# Part 4 practice
check("deck practice 1, 45 members, n=4", simple_random(ROW4, 1, 45, 4).sample,
      [38, 43, 6, 13])
r = systematic(ROW1, 1, 70, 7)
check("deck practice 2, 70 members, n=7, the 68 trap", r.sample,
      [5, 15, 25, 35, 45, 55, 65])
check("deck practice 2, 68 is rejected as over the interval",
      (r.steps[0].value, r.steps[0].reason), (68, "over interval"))
check("deck practice 3, 600 students, n=40, strata sizes",
      [s.count for s in strata_shares(
          [Stratum("Y9", 1, 210), Stratum("Y10", 211, 405), Stratum("Y11", 406, 600)], 40)],
      [14, 13, 13])

# --- Random number tables worksheet ----------------------------------------
check("worksheet Q1, 01-48, n=6",
      simple_random("63 17 42 90 05 17 38 71 48 26 09 55 31", 1, 48, 6).sample,
      [17, 42, 5, 38, 48, 26])
check("worksheet Q2, 001-350, n=5, read in threes",
      simple_random("27 45 19 08 33 50 91 22 74 00 01 46 33 87", 1, 350, 5).sample,
      [274, 83, 350, 146, 338])

ws3 = [Stratum("Swimming", 1, 20), Stratum("Pitch", 21, 40), Stratum("Other", 41, 50)]
check("worksheet Q3, sizes 20/20/10, n=5",
      [s.count for s in strata_shares(ws3, 5)], [2, 2, 1])
r = stratified("72 14 33 08 61 11 33 47 90 26 05 38", ws3, 5)
check("worksheet Q3, picks", [r.picks[k] for k in ("Swimming", "Pitch", "Other")],
      [[14, 8], [33, 26], [47]])

WS4 = ("08 75 63 01 22 29 08 79 04 10 50 46 00 01 18 75 21 64 23 31 97 42")
check("worksheet Q4, simple random from 001-240, n=6",
      simple_random(WS4, 1, 240, 6).sample, [87, 12, 229, 105, 46, 118])
ws4 = [Stratum("Adult", 1, 120), Stratum("Junior", 121, 200), Stratum("Senior", 201, 240)]
check("worksheet Q4, stratified sizes 120/80/40, n=6",
      [s.count for s in strata_shares(ws4, 6)], [3, 2, 1])
r = stratified(WS4, ws4, 6)
check("worksheet Q4, stratified picks",
      [r.picks[k] for k in ("Adult", "Junior", "Senior")],
      [[87, 12, 105], [164, 197], [229]])

r = systematic("47 83 19 15 00 09 62 30 71 04 52 88", 0, 599, 40)
check("worksheet Q5, tickets 000-599, n=40, interval", r.interval, 15)
check("worksheet Q5, 15 is rejected as the start (boundary)",
      [(s.value, s.action) for s in r.steps][:5],
      [(47, "reject"), (83, "reject"), (19, "reject"), (15, "reject"), (0, "accept")])
check("worksheet Q5, first four tickets", r.sample[:4], [0, 15, 30, 45])
check("worksheet Q5, last ticket", r.sample[-1], 585)
check("worksheet Q5, start is read in pairs even though tickets are three digits",
      start_read_width(0, 599, 40), 2)

# --- CA1 retake -------------------------------------------------------------
check("retake Q2, 300 parcels 000-299, n=4, read in threes",
      simple_random("48 71 62 00 09 31 16 20 45 27 85 36", 0, 299, 4).sample,
      [162, 0, 45, 278])
rt3 = [Stratum("Junior", 1, 30), Stratum("Senior", 31, 50), Stratum("Veteran", 51, 60)]
check("retake Q3, sizes", [s.count for s in strata_shares(rt3, 6)], [3, 2, 1])
r = stratified("74 18 52 09 18 36 88 27 57 41 63 05", rt3, 6)
check("retake Q3, picks", [r.picks[k] for k in ("Junior", "Senior", "Veteran")],
      [[18, 9, 27], [36, 41], [52]])
check("retake Q3, 57 is skipped because the Veterans are already full",
      next((s.reason for s in r.steps if s.value == 57), None), "group full")
r = systematic("68 93 57 24 05 81 46 30 19 72", 1, 400, 8)
check("retake Q4, 400 bottles, interval", r.interval, 50)
check("retake Q4, start", r.start, 24)
check("retake Q4, first four bottles", r.sample[:4], [24, 74, 124, 174])

# --- Cambridge's own published questions ------------------------------------
# 0479 2027 specimen paper 2 Q2(b): 30 students, simple random then systematic.
SPEC = "21 15 09 10 28 02"
check("0479 specimen P2 Q2(b)(i), 30 students, n=6",
      simple_random(SPEC, 1, 30, 6).sample, [21, 15, 9, 10, 28, 2])
check("0479 specimen P2 Q2(b)(ii), 30 students, n=6, interval", interval(30, 6), 5)
check("0479 specimen P2 Q2(b)(ii), the published sample",
      systematic("04 09 14 19 24 29", 1, 30, 6).sample, [4, 9, 14, 19, 24, 29])

# 4040 Nov 2023 p22 Q3(b): 84 shirts, three machines, sample of 7.
check("4040 Nov 2023 p22 Q3(b)(i), sizes 36/36/12 of 84, n=7",
      [s.count for s in strata_shares(
          [Stratum("A", 1, 36), Stratum("B", 37, 72), Stratum("C", 73, 84)], 7)],
      [3, 3, 1])
# 4040 Nov 2024 p22 Q8(d): systematic, interval 11, start 2.
check("4040 Nov 2024 p22 Q8(d), interval 11 from a start of 02",
      systematic("02", 1, 66, 6).sample, [2, 13, 24, 35, 46, 57])

# --- marking -----------------------------------------------------------------
check("full sample scores full marks", mark_sample([5, 41, 23], [5, 41, 23], 3).marks, 3)
check("one wrong number loses one mark", mark_sample([5, 41, 23], [5, 41, 24], 3).marks, 2)
check("one omission loses one mark", mark_sample([5, 41, 23], [5, 41], 3).marks, 2)
check("two errors leave one mark", mark_sample([5, 41, 23], [5, 7, 9], 3).marks, 1)
check("order does not matter", mark_sample([5, 41, 23], [23, 5, 41], 3).marks, 3)

# --- reading the table -------------------------------------------------------
check("printed in pairs", in_pairs("487162000931"), "48 71 62 00 09 31")
check("read in threes", read_blocks("48 71 62 00 09 31", 3),
      ["487", "162", "000", "931"])
check("a trailing part block is dropped", read_blocks("12345", 3), ["123"])

bad = [c for c in checks if not c[0]]
for ok, name, got, want in checks:
    if not ok:
        print(f"FAIL  {name}\n      got  {got}\n      want {want}")
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
