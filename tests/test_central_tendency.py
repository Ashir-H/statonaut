"""The central tendency topic: the arithmetic, the content files and the notes page.

Every figure checked in the first section is one recorded in the unit notes, so
a change to the engine that would alter a published answer fails here rather
than in a lesson.

The sweep in the third section is the one that matters most. No question in the
4040 archive has a tied highest frequency and no mark scheme says how to mark
one, so a generated question with a tie would be unmarkable. The sweep asserts
the generator never produces one.
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from streamlit.testing.v1 import AppTest  # noqa: E402

from app import registry  # noqa: E402
from app.topics.central_tendency import content, engine, generate  # noqa: E402
from app.topics.central_tendency.engine import Row  # noqa: E402
from app.topics.central_tendency.pages import notes  # noqa: E402

problems = []


def check(label, got, want):
    same = got == want
    if not same and isinstance(want, float) and isinstance(got, (int, float)):
        same = abs(got - want) < 1e-9
    if not same:
        problems.append(f"{label}: got {got!r}, want {want!r}")


def rows(xs, fs):
    return [Row(x, f) for x, f in zip(xs, fs)]


# ---- 1. the figures recorded in the unit notes ------------------------------

a = engine.solve_list([3, 4, 4, 4, 6, 7, 9, 11])
check("books: mode", a.mode, 4)
check("books: median", a.median, 5.0)
check("books: mean", a.mean, 6.0)
check("books: range", a.spread, 8)
check("books: position", a.position, 4.5)
check("books: middle values", a.middle_values, (4, 6))

a = engine.solve_list([8, 9, 9, 9, 10, 11, 12, 15, 25])
check("puzzle: mode", a.mode, 9)
check("puzzle: median", a.median, 10.0)
check("puzzle: mean", a.mean, 12.0)
check("puzzle: range", a.spread, 17)

t = engine.solve_table(rows(range(5), [7, 9, 8, 4, 2]))
check("pets: sigma fx", t.sigma_fx, 45)
check("pets: mean", t.mean, 1.5)
check("pets: running", t.running, (7, 16, 24, 28, 30))
check("pets: median", t.median, 1.0)
check("pets: mode", t.mode, 1)

t = engine.solve_table(rows([2, 5, 8, 12, 14, 16, 18], [4, 6, 7, 13, 8, 4, 3]))
check("courses: sigma f", t.sigma_f, 45)
check("courses: sigma fx", t.sigma_fx, 480)
check("courses: mean to 3sf", engine.shown(t.mean), "10.7")
check("courses: position", t.position, 23.0)
check("courses: median", t.median, 12.0)
check("courses: mode", t.mode, 12)

t = engine.solve_table(rows(range(6), [6, 11, 10, 8, 3, 2]))
check("goals: sigma fx", t.sigma_fx, 77)
check("goals: mean exact", t.mean, 1.925)
check("goals: mean to 3sf", engine.shown(t.mean), "1.93")
check("goals: median", t.median, 2.0)
check("goals: mode", t.mode, 1)

check("add 20: mean",
      engine.shown(engine.solve_list([3, 4, 4, 4, 6, 7, 9, 11, 20]).mean), "7.56")
check("remove 11: mean",
      engine.shown(engine.solve_list([3, 4, 4, 4, 6, 7, 9]).mean), "5.29")

a = engine.solve_list([18, 19, 20, 21, 22, 120])
check("salaries: mean to 3sf", engine.shown(a.mean), "36.7")
check("salaries: median", a.median, 20.5)
print("figures: every answer recorded in the unit notes is reproduced")

# ---- 2. rounding and the marking tolerance ---------------------------------

check("1.925 rounds up, as the scheme has it", engine.rounded(1.925, 3), 1.93)
check("exact answer accepted", engine.agrees(480 / 45, 480 / 45), True)
check("3sf accepted", engine.agrees(480 / 45, 10.7), True)
check("4sf accepted", engine.agrees(480 / 45, 10.67), True)
check("under-rounded refused", engine.agrees(480 / 45, 10.6), False)
check("blank refused", engine.agrees(5, None), False)
print("rounding: half upwards to three significant figures, and marked to 3sf")

# ---- 3. no generated question can tie --------------------------------------

check("bimodal list has no mode", engine.mode_of([8, 6, 7, 6, 7, 6, 2, 7, 5, 4]), None)
check("all values distinct, no mode", engine.mode_of([1, 2, 3, 4]), None)
check("tied table has no mode", engine.solve_table(rows([1, 2, 3], [5, 5, 2])).mode,
      None)

unmarkable = []
pre_ordered = []
out_of_range = []
for seed in range(1000, 2500):
    for kind in ("list", "table"):
        question = generate.build(kind, seed)
        answers = generate.solve(question)
        if answers.mode is None:
            unmarkable.append((kind, seed))
        if kind == "list":
            if list(question["values"]) == sorted(question["values"]):
                pre_ordered.append(seed)
        elif not 25 <= answers.sigma_f <= 60:
            out_of_range.append(seed)
if unmarkable:
    problems.append(f"{len(unmarkable)} question(s) have no single mode, so no mark "
                    f"scheme covers them: e.g. {unmarkable[:3]}")
if pre_ordered:
    problems.append(f"{len(pre_ordered)} list question(s) arrive already in order, "
                    f"which gives away the mark for ordering: e.g. {pre_ordered[:3]}")
if out_of_range:
    problems.append(f"{len(out_of_range)} table(s) have a total outside 25 to 60: "
                    f"e.g. {out_of_range[:3]}")
print("generator: 3000 questions, every one with a single mode, no list pre-ordered")

# ---- 4. the content files --------------------------------------------------

complaints = content.check()
problems += complaints

AHEAD = ("class boundar", "mid-point", "midpoint", "modal class", "interpolat",
         "cumulative frequency")
for name in content.MEASURES:
    body = "\n".join(content.measure(name).bodies.values())
    if body.count("$") % 2:
        problems.append(f"{name}.md has unbalanced dollars")
    for banned in AHEAD:
        if banned in body.lower():
            problems.append(f"{name}.md teaches '{banned}', which belongs to the "
                            f"grouped unit taught after this one")

closing = content.closing()
if closing.section(content.RANGE).count("$") % 2:
    problems.append("closing.md has unbalanced dollars")
later = closing.section(content.LATER).lower()
if not any(ahead in later for ahead in AHEAD):
    problems.append("closing.md does not warn that grouped data changes the method, "
                    "which is the one thing that section exists to say")
words = closing.section(content.WORDS).lower()
if "measure of central tendency" not in words and "measures of central" not in words:
    problems.append("closing.md does not explain the phrase the syllabus uses")
print("content:", "no complaints" if not complaints else complaints)

# ---- 5. the notes page -----------------------------------------------------


def open_page(page_key):
    script = (
        "import sys\n"
        f"sys.path.insert(0, {str(ROOT / 'src')!r})\n"
        "from app import registry\n"
        "topic = next(t for t in registry.topics() if t.key == 'central-tendency')\n"
        f"topic.page({page_key!r}).render()\n"
    )
    return AppTest.from_string(script, default_timeout=90).run()


def complain(where, at):
    for e in at.exception:
        problems.append(f"{where}: {e.value}")


topic = next(t for t in registry.topics() if t.key == "central-tendency")
if topic.unit != "Unit 5":
    problems.append(f"the topic is registered as {topic.unit}, not Unit 5")
if [p.key for p in topic.pages] != ["notes"]:
    problems.append(f"this commit should register the notes page only, "
                    f"not {[p.key for p in topic.pages]}")

at = open_page("notes")
complain("notes load", at)
opening = " ".join(m.value for m in at.markdown)
if "central tendency" not in opening.lower():
    problems.append("the notes page does not open with the vocabulary note")

for key, label in notes.CHOICES.items():
    at.segmented_control(key="ct-notes:choice").set_value(key).run()
    complain(f"notes '{label}'", at)
    body = " ".join(m.value for m in at.markdown)
    if key == "closing":
        wanted = ("The range", "What comes later")
    else:
        wanted = ("How it is computed", "When it is used", "How it is marked")
    for heading in wanted:
        if heading not in body:
            problems.append(f"notes '{label}': '{heading}' is missing")
    if key in content.MEASURES:
        if not at.expander:
            problems.append(f"notes '{label}': the worked example is missing")
        shown = " ".join(m.value for m in at.markdown)
        if "so the " + key not in shown.lower():
            problems.append(f"notes '{label}': the example never states the answer")
    print(f"notes: '{label}' shows {'both closing notes' if key == 'closing' else 'all four parts with a worked example'}")

# the example is the same every time, so a lesson can refer to it
first = generate.build("list", 1204)["values"]
second = generate.build("list", 1204)["values"]
if first != second:
    problems.append("the worked example changes between runs")
print("notes: the worked example is fixed, so a lesson can refer to it")

print()
if problems:
    print(f"{len(problems)} PROBLEM(S):")
    for p in problems:
        print("  -", p)
    sys.exit(1)
print("central tendency: the arithmetic matches the notes, no question can tie, "
      "and the notes page reads one measure at a time")
