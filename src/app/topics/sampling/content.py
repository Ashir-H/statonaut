"""Teaching text and the question bank.

The wording of the rules follows the conventions recorded for this course in
claude/unit1-data-and-its-collection.md, claude/cambridge-source-evidence-topic1.md
and claude/4040-past-paper-index.md. Where a mark scheme is quoted, the paper
is named so a student can be shown the original.
"""

from typing import Dict, List

from .engine import Stratum

# ------------------------------------------------------------- the one rule

READING = """
### First, decide how wide the numbers are

A random number table is printed in pairs of digits, but the pairs are only
how it is printed. **You read it in blocks as wide as the labels you are
choosing from.**

| The population is numbered | Read the table in | Example |
|---|---|---|
| 01 to 60 | blocks of **two** digits | `68 05 41` is 68, 05, 41 |
| 001 to 350 | blocks of **three** digits | `27 45 19 08` is 274, 519, 08... |
| 000 to 599 | blocks of **three** digits | 000 is a real member, not nothing |

Start at the left of the row you are told to use and work along it. Never go
back, never skip ahead to find a number you like, and **never round a rejected
number into range**.
"""

METHODS: Dict[str, Dict[str, str]] = {
    "simple": {
        "title": "Simple random sample",
        "idea": """
Every member of the population has an equal chance of being chosen, and so
does every possible sample. You need a **sampling frame**: a numbered list of
the whole population.
""",
        "steps": """
1. Number the population, using the same number of digits for every member.
2. Read the table in blocks of that width.
3. **Reject** any number outside the numbered range.
4. **Reject** any number you have already chosen.
5. Stop as soon as you have the sample size asked for.
""",
        "watch": """
- `00` or `000` is a real member when the numbering starts at zero, and is not
  a member when the numbering starts at 01.
- The highest label is a member. For 01 to 48, **48 is in** and 49 is out.
- A repeat is rejected, not re-used. The sample is a set of different members.
""",
        "marks": """
Cambridge marks the **sample you end up with**, not the rejections. Nov 2023
paper 22 Q3(b)(ii) awards `B3, (B2 for 1 error/omission), (B1 for 2
errors/omissions)`, so a correct sample scores full marks even if no working
is shown. Show your rejections anyway: it is how you find your own mistakes,
and it protects you when the sample comes out wrong.
""",
    },
    "systematic": {
        "title": "Systematic sample",
        "idea": """
Choose every *k*th member of the population, starting from a random point.
The table is used **once only**, to find that starting point. Everything
after it is arithmetic.
""",
        "steps": """
1. Find the interval: **k = population size / sample size**.
2. The random start must be one of the first *k* members, so read the table in
   blocks wide enough for the **largest possible start**, which is *k* - not
   the width of the population labels.
3. Take the first number in the table that could be a start.
4. Add *k* each time until you have the whole sample.
""",
        "watch": """
- A number can be a real member of the population and still be **rejected as a
  start** because it is bigger than the interval. With 70 members and a sample
  of 7, the interval is 10, so 68 is a member but cannot be the start.
- The interval decides the block width. With 400 bottles and a sample of 8 the
  interval is 50, so the start is read in **pairs**, even though the bottles
  are numbered 001 to 400.
- Check the last member of your sample is still inside the population.
""",
        "marks": """
0479 2027 specimen paper 2 Q2(b)(ii) awards `M1 method, M1 interval, A1
accuracy` - the interval carries a mark of its own, so always write it down.
""",
    },
    "stratified": {
        "title": "Stratified sample",
        "idea": """
The population splits into groups (strata). Each group contributes members **in
proportion to its size**, so the sample has the same make-up as the population.
""",
        "steps": """
1. For each group: **group size / population size x sample size**. Write the
   calculation, not just the answer.
2. Check the group sizes add up to the sample size.
3. Read along the table **once**. Send each number to the group it belongs to.
4. **Skip** a number whose group is already full, and carry on reading.
5. Stop when every group is full.
""",
        "watch": """
- One pass along the table, not a fresh pass for each group. This is how
  Cambridge does it: a number is ignored "if the machine to which it relates
  has not yet been fully sampled" (Nov 2023 paper 22 Q3(b)(ii)).
- Finishing the proportions is only half the question. You must then select
  the members inside each group.
- A skipped number is not a mistake, and it is not a repeat: the member exists,
  its group is simply finished.
""",
        "marks": """
Nov 2023 paper 22 Q3(b)(i) awards `M1` for any **one** correct proportion and
`A1` for all of the group sizes, so a single correct line of working earns a
mark even if the rest goes wrong. The selection is then marked like any other
random-number sample.
""",
    },
}

REPRESENTATIVE = """
### Is this sample representative?

Syllabus 1.4 asks you to *show* whether a sample is representative "in terms
of one or more of the strata". A bare yes or no scores nothing. The answer has
three parts:

1. The sample's **actual** make-up.
2. The make-up you would **expect**, from group size / population x sample size.
3. A **conclusion** that compares the two.

> A sample of 4 parcels contains 3 local and 1 international. Expected:
> 225/300 x 4 = 3 local and 75/300 x 4 = 1 international. The sample matches
> the expected numbers, so it is representative.
"""

INTERVAL_MARKS = """
Nov 2023 paper 22 Q3(a) awards `M1` for the difference between the two members
and `A1` for the population divided by that difference. Cambridge asks for the
**smallest possible** sample size, because the two members given are not said
to be next to each other in the sample.
"""

EXAM_NOTES = """
### What the examiner is actually looking at

**The sample, not the working.** For every random-number selection in the
archive the marks sit on the numbers you produce. Partial credit runs down a
ladder: all correct, then one error or omission, then two.

**The interval, written down.** In a systematic question the interval is a
mark in its own right.

**One proportion, written out.** In a stratified question one correct
`group/population x sample` line earns a method mark even if the arithmetic
after it is wrong.

**`oe`, everywhere.** "Or equivalent" appears 234 times across the 40 mark
schemes in our archive. Your wording does not have to match the mark scheme's
wording; it has to mean the same thing.

**Every Paper 2 in the last five years has a random number table question.**
It is the most reliable topic in the paper.
"""

MISCONCEPTIONS = [
    ("Rounding a rejected number into range",
     "89 is not 'nearly 60'. Out of range means read the next number."),
    ("Reading single digits when the labels are two digits",
     "The block width follows the labels, not the way the table is printed."),
    ("Forgetting to reject a repeat",
     "A member already chosen cannot be chosen twice."),
    ("Taking the first in-range member as a systematic start",
     "The start must be within the first interval, not just inside the population."),
    ("Stopping a stratified question after the proportions",
     "The proportions are the first mark. Then you still have to select."),
    ("A sample that does not add up",
     "The group sizes must total the sample size asked for."),
    ("'Just ask more people'",
     "A biased method stays biased however large the sample."),
]

# ------------------------------------------------------------ question bank

ROW1 = "68 05 41 05 89 23 60 17 74 36 91 08 52 66 30 47"
ROW2 = "74 21 09 63 30 86 12 45 07 58 93 26 51 04 77 39"
ROW3 = "79 06 41 18 36 06 29 02 15 88 53 67 24 90 11 44"
ROW4 = "97 38 69 43 06 89 13 44 91 40 65 52 05 88 03 34"

BANK: List[Dict] = [
    {
        "id": "deck-1",
        "source": "Unit 1 deck, worked example (Part 4)",
        "kind": "simple",
        "setting": "A year group has 60 students. They are numbered 01 to 60.",
        "task": "Use the table to select a simple random sample of 5 students.",
        "lo": 1, "hi": 60, "n": 5, "row": ROW1, "marks": 2,
        "note": "Two numbers are out of range and one is a repeat.",
    },
    {
        "id": "deck-2",
        "source": "Unit 1 deck, worked example (Part 4)",
        "kind": "systematic",
        "setting": "The same 60 students, numbered 01 to 60.",
        "task": "Use the table to select a systematic sample of 6 students.",
        "lo": 1, "hi": 60, "n": 6, "row": ROW2, "marks": 3,
        "note": "The interval is 10, so the start must be between 01 and 10. "
                "74 and 21 are both real students, and both are rejected.",
    },
    {
        "id": "deck-3",
        "source": "Unit 1 deck, Part 4 practice 1",
        "kind": "simple",
        "setting": "A club has 45 members, numbered 01 to 45.",
        "task": "Select a simple random sample of 4 members.",
        "lo": 1, "hi": 45, "n": 4, "row": ROW4, "marks": 2,
        "note": "",
    },
    {
        "id": "deck-4",
        "source": "Unit 1 deck, Part 4 practice 2",
        "kind": "systematic",
        "setting": "A club has 70 members, numbered 01 to 70.",
        "task": "Select a systematic sample of 7 members.",
        "lo": 1, "hi": 70, "n": 7, "row": ROW1, "marks": 3,
        "note": "The trap: 68 is a member of the club, but the interval is 10, "
                "so it cannot be the random start.",
    },
    {
        "id": "ws-1",
        "source": "Random number tables worksheet, Q1",
        "kind": "simple",
        "setting": "A population of 48 is numbered 01 to 48.",
        "task": "Select a simple random sample of 6.",
        "lo": 1, "hi": 48, "n": 6, "row": "63 17 42 90 05 17 38 71 48 26 09 55 31",
        "marks": 3,
        "note": "48 is a boundary that should be accepted. 17 appears twice.",
    },
    {
        "id": "ws-2",
        "source": "Random number tables worksheet, Q2",
        "kind": "simple",
        "setting": "A population of 350 is numbered 001 to 350.",
        "task": "Select a simple random sample of 5.",
        "lo": 1, "hi": 350, "n": 5,
        "row": "27 45 19 08 33 50 91 22 74 00 01 46 33 87", "marks": 3,
        "note": "Printed in pairs, read in threes. 350 is in; 000 is not a member "
                "because the numbering starts at 001.",
    },
    {
        "id": "ws-3",
        "source": "Random number tables worksheet, Q3",
        "kind": "stratified",
        "setting": "A population of 50 splits into three groups: "
                   "Group S numbered 01-20, Group P numbered 21-40, Group O numbered 41-50.",
        "task": "Show that the sample of 5 contains 2, 2 and 1, then select it.",
        "n": 5,
        "strata": [Stratum("Group S", 1, 20), Stratum("Group P", 21, 40),
                   Stratum("Group O", 41, 50)],
        "row": "72 14 33 08 61 11 33 47 90 26 05 38", "marks": 3,
        "note": "One pass along the table. 11 and 05 are skipped because Group S "
                "is already full.",
    },
    {
        "id": "ws-4",
        "source": "Random number tables worksheet, Q4",
        "kind": "stratified",
        "setting": "A population of 240 splits into three groups: "
                   "Group A numbered 001-120, Group J numbered 121-200, "
                   "Group S numbered 201-240.",
        "task": "Select a stratified sample of 6.",
        "n": 6,
        "strata": [Stratum("Group A", 1, 120), Stratum("Group J", 121, 200),
                   Stratum("Group S", 201, 240)],
        "row": "08 75 63 01 22 29 08 79 04 10 50 46 00 01 18 75 21 64 23 31 97 42",
        "marks": 3,
        "note": "The same table read for a simple random sample gives 5 from Group A, "
                "none from J and 1 from S - which is why the stratified method exists.",
    },
    {
        "id": "ws-5",
        "source": "Random number tables worksheet, Q5",
        "kind": "systematic",
        "setting": "Raffle tickets are numbered 000 to 599.",
        "task": "Select a systematic sample of 40 tickets.",
        "lo": 0, "hi": 599, "n": 40, "row": "47 83 19 15 00 09 62 30 71 04 52 88",
        "marks": 3,
        "note": "The interval is 15, so the start is read in pairs and must be "
                "00 to 14. 15 itself is one too big, and 00 is a real ticket.",
    },
    {
        "id": "retake-2",
        "source": "Class Assessment 1 retake, Q2",
        "kind": "simple",
        "setting": "A depot has 300 parcels numbered 000 to 299. "
                   "Parcels 000-224 are local and 225-299 are international.",
        "task": "Select a simple random sample of 4 parcels.",
        "lo": 0, "hi": 299, "n": 4, "row": "48 71 62 00 09 31 16 20 45 27 85 36",
        "marks": 2,
        "note": "Read in pairs this row begins 48, 71, 62 and gives nothing away. "
                "Regroup into threes. Parcel 000 is real and is selected second.",
    },
    {
        "id": "retake-3",
        "source": "Class Assessment 1 retake, Q3",
        "kind": "stratified",
        "setting": "A club of 60: Juniors numbered 01-30, Seniors 31-50, Veterans 51-60.",
        "task": "Find the number needed from each group, then select the sample of 6.",
        "n": 6,
        "strata": [Stratum("Junior", 1, 30), Stratum("Senior", 31, 50),
                   Stratum("Veteran", 51, 60)],
        "row": "74 18 52 09 18 36 88 27 57 41 63 05", "marks": 3,
        "note": "57 is a real Veteran, but the Veterans are already full, so it is "
                "skipped. So is 05.",
    },
    {
        "id": "retake-4",
        "source": "Class Assessment 1 retake, Q4",
        "kind": "systematic",
        "setting": "A factory has 400 bottles numbered 001 to 400.",
        "task": "Select a systematic sample of 8 bottles.",
        "lo": 1, "hi": 400, "n": 8, "row": "68 93 57 24 05 81 46 30 19 72",
        "marks": 3,
        "note": "The interval is 50, so the start is read in pairs even though the "
                "bottles have three-digit labels.",
    },
]
