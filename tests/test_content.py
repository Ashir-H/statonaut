"""The content files: readable by the app, and still giving the printed answers.

The questions in `content/sampling/questions.toml` were set in class and their
answers are recorded in the project notes. This checks that editing the file
has not changed any of them, and that every question can be completed from the
row it is given.

Needs Python 3.11 or newer, for tomllib.
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from app.core.library import ContentError  # noqa: E402
from app.topics.sampling import content, engine  # noqa: E402

problems = []

# ---- the files are all there, with the headings the pages read -------------
complaints = content.check()
problems += complaints
print("content check:", "no complaints" if not complaints else complaints)

bank = content.questions()
print(f"questions.toml: {len(bank)} questions")

# ---- every question can be finished from the row it is given ---------------
for q in bank:
    if q["kind"] == "simple":
        result = engine.simple_random(q["row"], q["lo"], q["hi"], q["n"])
    elif q["kind"] == "systematic":
        result = engine.systematic(q["row"], q["lo"], q["hi"], q["n"])
    else:
        result = engine.stratified(q["row"], q["strata"], q["n"])
    if not result.complete:
        problems.append(f"{q['id']}: the row runs out before the sample is full "
                        f"(got {engine.pad_all(result.sample, result.width)})")

# ---- and still gives the answer printed on the paper -----------------------
# From claude/unit1-data-and-its-collection.md, claude/worksheet-random-number-tables.md
# and claude/ca1-retake.md. A failure here means a row or a range was changed.
PRINTED = {
    "deck-1": ["05", "41", "23", "60", "17"],
    "deck-2": ["09", "19", "29", "39", "49", "59"],
    "deck-3": ["38", "43", "06", "13"],
    "deck-4": ["05", "15", "25", "35", "45", "55", "65"],
    "ws-1": ["17", "42", "05", "38", "48", "26"],
    "ws-2": ["274", "083", "350", "146", "338"],
    "ws-5": ["000", "015", "030", "045"],
    "retake-2": ["162", "000", "045", "278"],
    "retake-4": ["024", "074", "124", "174"],
}
PRINTED_GROUPS = {
    "ws-3": {"Group S": ["14", "08"], "Group P": ["33", "26"], "Group O": ["47"]},
    "ws-4": {"Group A": ["087", "012", "105"], "Group J": ["164", "197"],
             "Group S": ["229"]},
    "retake-3": {"Junior": ["18", "09", "27"], "Senior": ["36", "41"],
                 "Veteran": ["52"]},
}

by_id = {q["id"]: q for q in bank}
for qid, printed in PRINTED.items():
    q = by_id.get(qid)
    if q is None:
        problems.append(f"{qid} is no longer in questions.toml")
        continue
    if q["kind"] == "simple":
        result = engine.simple_random(q["row"], q["lo"], q["hi"], q["n"])
    else:
        result = engine.systematic(q["row"], q["lo"], q["hi"], q["n"])
    got = engine.pad_all(result.sample, result.width)
    if got[:len(printed)] != printed or len(got) != q["n"]:
        problems.append(f"{qid}: answer is now {got[:len(printed)]} "
                        f"(length {len(got)}), the paper says {printed} "
                        f"(length {q['n']})")

for qid, printed in PRINTED_GROUPS.items():
    q = by_id.get(qid)
    if q is None:
        problems.append(f"{qid} is no longer in questions.toml")
        continue
    result = engine.stratified(q["row"], q["strata"], q["n"])
    got = {name: engine.pad_all(vs, result.width) for name, vs in result.picks.items()}
    if got != printed:
        problems.append(f"{qid}: answer is now {got}, the paper says {printed}")

print(f"printed answers: {len(PRINTED) + len(PRINTED_GROUPS)} questions checked "
      "against the papers")

# ---- a missing file or heading is reported, not raised at the page ---------
try:
    content.LIBRARY.text("no-such-file")
    problems.append("a missing file did not raise ContentError")
except ContentError as exc:
    if "no-such-file" not in str(exc):
        problems.append(f"unhelpful message for a missing file: {exc}")
try:
    content.method("simple").section("not-a-heading")
    problems.append("a missing heading did not raise ContentError")
except ContentError:
    pass
print("missing files and headings: reported with the file named")

print()
if problems:
    print(f"{len(problems)} PROBLEM(S):")
    for p in problems:
        print("  -", p)
    sys.exit(1)
print("content: files load, headings present, printed answers unchanged")
