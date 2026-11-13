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
from app.topics.central_tendency import (choosing, content,  # noqa: E402
                                         engine, generate, ordering)
from app.topics.central_tendency.engine import Row  # noqa: E402
from app.topics.central_tendency.pages import notes, table_walk  # noqa: E402,F401
from app.topics.central_tendency.shared import (ROUNDING, mean_working,  # noqa: E402
                                                value_text)

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

# Both roundings are asked for, so both are accepted. Which one is coarser
# depends on the size of the number, so neither can be derived from the other.
check("1.5 is exact", engine.is_exact(1.5), True)
check("5/6 is not exact", engine.is_exact(5 / 6), False)
check("two decimal places of 5/6", engine.to_places(5 / 6), 0.83)
check("2 d.p. accepted", engine.agrees(5 / 6, 0.83), True)
check("3 s.f. accepted", engine.agrees(5 / 6, 0.833), True)
check("coarser than both refused", engine.agrees(5 / 6, 0.8), False)

# A rounded answer is written with an approximately-equals sign.
if "approx" not in mean_working(480, 45, 480 / 45):
    problems.append("a rounded mean is written with an equals sign")
if "approx" in mean_working(45, 30, 1.5):
    problems.append("an exact mean is written with an approximately-equals sign")
if "approx" not in value_text(480 / 45):
    problems.append("a rounded value on its own is not marked as approximate")
if "approx" in value_text(1.5):
    problems.append("an exact value on its own is called approximate")
if "two decimal places" not in ROUNDING:
    problems.append("the rounding instruction does not offer two decimal places")
print("rounding: three significant figures or two decimal places, both accepted, "
      "and a rounded answer is written with an approximately-equals sign")

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

vocab = content.vocabulary()
if "\n".join(vocab.bodies.values()).count("$") % 2:
    problems.append("vocabulary.md has unbalanced dollars")
words = vocab.section(content.WORDS).lower()
if "measure of central tendency" not in words and "measures of central" not in words:
    problems.append("vocabulary.md does not explain the phrase the syllabus uses")

# The product is set as mathematics with a centre dot. A multiplication sign
# between f and x reads as two x's at body-text size.
for name in content.MEASURES:
    body = "\n".join(content.measure(name).bodies.values())
    if "\u00d7" in body or "\\times" in body:
        problems.append(f"{name}.md writes the product with a multiplication sign "
                        f"instead of a centre dot")
if "\\cdot" not in content.measure("mean").section(content.COMPUTED):
    problems.append("mean.md does not set the product as mathematics")
prompts = " ".join(step["ask"]
                   for step in table_walk.walk_steps(
                       generate.solve(generate.build("table", 1204))))
if "\u00d7" in prompts:
    problems.append("the walkthrough prompts still carry a multiplication sign")
if "\\cdot" not in prompts:
    problems.append("the walkthrough prompts do not set the product as mathematics")
if "two decimal places" not in prompts:
    problems.append("the walkthrough never says how to round the mean")
print("content:", "no complaints" if not complaints else complaints)

# ---- 5. the ordering exercise ----------------------------------------------

page = ordering.ordering_html([3, 9, 4], theme="dark")
for value in (3, 9, 4):
    if str(value) not in page:
        problems.append(f"the ordering exercise does not contain the value {value}")
if "[3, 9, 4]" not in page:
    problems.append("the ordering exercise does not receive the values in the order "
                    "the question gives them")
# Touch has to work: the drag-and-drop API does nothing on a phone, and the
# chips must not scroll the page while being dragged.
for needed, why in [
        ("pointerdown", "dragging is not built on pointer events, so it will not "
                        "work on a touch screen"),
        ("touch-action", "a chip will scroll the page instead of being dragged"),
        ("prefers-reduced-motion", "the movement cannot be turned off"),
        ("window.parent", "the colours are not read from the app, so dark mode "
                          "will be wrong"),
        ("ArrowLeft", "there is no keyboard route through the exercise")]:
    if needed not in page:
        problems.append(f"the ordering exercise is missing '{needed}': {why}")
if "#edebe8" not in page:
    problems.append("the ordering exercise has no light-text fallback for dark mode")
for forbidden in ("<script src", "http://", "https://"):
    if forbidden in page:
        problems.append(f"the ordering exercise loads something external: {forbidden}")
if ordering.ordering_html([3, 9, 4], theme=None) == page:
    problems.append("the theme makes no difference to the exercise")
# Beside a marked question the same dragging must reveal nothing: the median
# and its position are two of that page's five marks.
working = ordering.ordering_html([3, 9, 4], theme="dark", mode=ordering.WORKING)
for leak in ("Check the order", "so the median", 'id="say"'):
    if leak in working:
        problems.append(f"the rough-work row contains {leak!r}, so a marked "
                        f"question could answer itself")
if "pointerdown" not in working or "ArrowLeft" not in working:
    problems.append("the rough-work row cannot be dragged or keyed")
if 'id="reset"' not in working:
    problems.append("the rough-work row cannot be put back to the given order")
if ordering.HEIGHTS[ordering.WORKING] >= ordering.HEIGHTS[ordering.LEARN]:
    problems.append("the rough-work row is no shorter than the exercise, though it "
                    "has no message to show")
print("ordering: values embedded in the question's own order, dragging works by "
      "pointer and by keyboard, nothing loaded from outside")
print("ordering: the rough-work mode drags but cannot check, print or reveal")

# ---- 6. the notes page -----------------------------------------------------


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
if [p.key for p in topic.pages] != ["notes", "walkthrough", "choosing", "practice"]:
    problems.append(f"expected notes, walkthrough, choosing and practice, "
                    f"not {[p.key for p in topic.pages]}")

at = open_page("notes")
complain("notes load", at)
opening = " ".join(m.value for m in at.markdown)
if "central tendency" not in opening.lower():
    problems.append("the notes page does not open with the vocabulary note")

if list(notes.CHOICES) != list(content.MEASURES):
    problems.append(f"the notes page offers {list(notes.CHOICES)}, which is not the "
                    f"three measures")

for key, label in notes.CHOICES.items():
    at.segmented_control(key="ct-notes:choice").set_value(key).run()
    complain(f"notes '{label}'", at)
    body = " ".join(m.value for m in at.markdown)
    for heading in ("How it is computed", "When it is used", "How it is marked"):
        if heading not in body:
            problems.append(f"notes '{label}': '{heading}' is missing")
    if not at.expander:
        problems.append(f"notes '{label}': the worked example is missing")
    if "so the " + key not in body.lower():
        problems.append(f"notes '{label}': the example never states the answer")
    print(f"notes: '{label}' shows all four parts with a worked example")

# the example is the same every time, so a lesson can refer to it
first = generate.build("list", 1204)["values"]
second = generate.build("list", 1204)["values"]
if first != second:
    problems.append("the worked example changes between runs")
print("notes: the worked example is fixed, so a lesson can refer to it")

# ---- 7. the frequency table walkthrough ------------------------------------

at = open_page("walkthrough")
complain("walkthrough load", at)
seed = at.session_state["ct-walk"]["seed"]
question = generate.build("table", seed)
answers = generate.solve(question)
steps = table_walk.walk_steps(answers)
signature = generate.signature(question)

for index, step in enumerate(steps):
    key = f"ct-walk:{signature}:{index}"
    try:
        at.text_input(key=key).set_value(engine.shown(step["want"])).run()
    except KeyError:
        problems.append(f"walkthrough step {index + 1} ({step['kind']}) never appeared")
        break
    at.button(key=f"ct-walk:check:{index}").click().run()
    complain(f"walkthrough step {index + 1}", at)
    reached = at.session_state["ct-walk:state"]["step"]
    if reached != index + 1:
        problems.append(f"walkthrough stuck at step {reached} after a correct answer "
                        f"to step {index + 1} ({step['kind']})")
        break
else:
    if not any("complete" in m.value for m in at.success):
        problems.append("the walkthrough never reported the table complete")
    filled = at.session_state["ct-walk:state"]
    if filled["fx"] != list(answers.products):
        problems.append(f"the f x column ended as {filled['fx']}, "
                        f"not {list(answers.products)}")
    if filled["run"] != list(answers.running):
        problems.append(f"the running total ended as {filled['run']}, "
                        f"not {list(answers.running)}")
print(f"walkthrough: all {len(steps)} steps of a {len(answers.rows)}-row table "
      f"accepted in order, both columns correct")

# a wrong value must hold the student on the same cell
at = open_page("walkthrough")
seed = at.session_state["ct-walk"]["seed"]
answers = generate.solve(generate.build("table", seed))
signature = f"table:{seed}"
wrong = engine.shown(table_walk.walk_steps(answers)[0]["want"] + 1)
at.text_input(key=f"ct-walk:{signature}:0").set_value(wrong).run()
at.button(key="ct-walk:check:0").click().run()
complain("walkthrough wrong answer", at)
if at.session_state["ct-walk:state"]["step"] != 0:
    problems.append("a wrong f x value still advanced the walkthrough")
if not at.error:
    problems.append("a wrong f x value drew no correction")
print("walkthrough: a wrong value holds the student on the same cell, with a reason")

# the steps come in the order the marks are paid in
kinds = [step["kind"] for step in steps]
last_fx = max(i for i, kind in enumerate(kinds) if kind == "fx")
if last_fx > kinds.index("sigma_fx"):
    problems.append("the f x column is added up before it is finished")
if kinds.index("sigma_fx") > kinds.index("mean"):
    problems.append("the mean is asked for before the total it is built from")
if kinds.index("sigma_f") > kinds.index("mean"):
    problems.append("the mean is asked for before the frequencies are totalled")
last_run = max(i for i, kind in enumerate(kinds) if kind == "run")
if last_run > kinds.index("position") or kinds.index("position") > kinds.index("median"):
    problems.append("the median is reached before the running total and the position")
print("walkthrough: the column before its total, the total before the mean, the "
      "running total before the median")

# ---- 8. the marked question ------------------------------------------------

for kind in ("list", "table"):
    at = open_page("practice")
    at.selectbox(key="ct-practice:choice").set_value(kind).run()
    complain(f"practice {kind} load", at)
    if "two decimal places" not in " ".join(m.value for m in at.markdown):
        problems.append(f"practice {kind}: the question does not say how to round")
    captions = " ".join(c.value for c in at.caption).lower()
    if kind == "list" and "drag" not in captions:
        problems.append("a list question offers no row to drag into order")
    if kind == "table" and "drag" in captions:
        problems.append("a table question offers a row to drag, but it has no list "
                        "to order: its median comes from the running total")
    seed = at.session_state["ct-practice"]["seed"]
    answers = generate.solve(generate.build(kind, seed))
    prefix = f"ct-practice:{kind}:{seed}"
    from_table = kind == "table"
    total = answers.sigma_fx if from_table else answers.total

    for key, value in [("mode", answers.mode), ("position", answers.position),
                       ("median", answers.median), ("total", total),
                       ("mean", answers.mean)]:
        at.text_input(key=f"{prefix}:{key}").set_value(engine.shown(value)).run()
    at.button(key=f"{prefix}:mark").click().run()
    complain(f"practice {kind} mark", at)
    banner = " ".join(m.value for m in at.success)
    if "5 out of 5" not in banner:
        problems.append(f"practice {kind}: a correct answer scored {banner!r}")
    else:
        print(f"practice: {kind:5} a correct answer with its working scored 5/5")

    at = open_page("practice")
    at.selectbox(key="ct-practice:choice").set_value(kind).run()
    seed = at.session_state["ct-practice"]["seed"]
    answers = generate.solve(generate.build(kind, seed))
    prefix = f"ct-practice:{kind}:{seed}"
    total = answers.sigma_fx if kind == "table" else answers.total
    # One away from every right answer, rather than a column of zeros: a table
    # whose values start at zero can make an all-zeros answer partly correct,
    # and then the question has not been marked wrong at all.
    for key, value in [("mode", answers.mode), ("position", answers.position),
                       ("median", answers.median), ("total", total),
                       ("mean", answers.mean)]:
        at.text_input(key=f"{prefix}:{key}").set_value(engine.shown(value + 1)).run()
    at.button(key=f"{prefix}:mark").click().run()
    complain(f"practice {kind} wrong", at)
    banner = " ".join(m.value for m in at.error)
    if not at.error:
        problems.append(f"practice {kind}: a wholly wrong answer was not marked wrong")
    elif "0 out of 5" not in banner:
        problems.append(f"practice {kind}: a wholly wrong answer scored {banner!r}")

# a part-filled answer is sent back rather than marked, so the score is not
# nudged by a half-finished attempt
at = open_page("practice")
seed = at.session_state["ct-practice"]["seed"]
kind = at.session_state["ct-practice"]["choice"]
prefix = f"ct-practice:{kind}:{seed}"
at.text_input(key=f"{prefix}:mode").set_value("1").run()
at.button(key=f"{prefix}:mark").click().run()
complain("practice part-filled", at)
if not at.warning:
    problems.append("a part-filled answer was marked instead of being sent back")

# the working is asked for separately, because that is what the marks are for
labels = [box.label for box in at.text_input]
if not any("position" in label.lower() for label in labels):
    problems.append("the question never asks for the median position, which is a "
                    "mark of its own")
# Compared without lowering: lower() turns the capital sigma into a small one.
if not any(label in ("\u03a3x", "\u03a3fx") for label in labels):
    problems.append(f"the question never asks for the total, which carries the "
                    f"method mark for the mean: boxes are {labels}")
print("practice: nothing for a wholly wrong answer, a part-filled answer is not "
      "marked at all, and the working is asked for separately")

# ---- 9. choosing a measure --------------------------------------------------

problems += choosing.complaints()
bank = choosing.situations()
if len(bank) < 6:
    problems.append(f"only {len(bank)} situation(s) in the bank, so a code comes "
                    f"round again too soon")
spread = {measure: sum(1 for item in bank if item.answer == measure)
          for measure in choosing.MEASURES}
for measure, count in spread.items():
    if count < 2:
        problems.append(f"only {count} situation(s) answered '{measure}', so the "
                        f"answer could be guessed from the kind of data alone")
if choosing.pick(1204).key != choosing.pick(1204).key:
    problems.append("a code does not give back the same situation")
first = bank[0]
if first.statements(1204) != first.statements(1204):
    problems.append("the statements are ordered differently on each run, so one code "
                    "does not give two students the same question")
if sorted(first.statements(1204)) != sorted([first.reason, *first.distractors]):
    problems.append("ordering the statements loses or adds one")
if first.statements(1204) == first.statements(1205):
    problems.append("the statements sit in the same order whatever the code, so the "
                    "position of the answer could be learned rather than the answer")
print(f"choosing: {len(bank)} situations, {spread}, each checked against its own data")

at = open_page("choosing")
complain("choosing load", at)
seed = at.session_state["ct-choose"]["seed"]
situation = choosing.pick(seed)
prefix = f"ct-choose:{situation.key}:{seed}"
at.radio(key=f"{prefix}:measure").set_value(situation.answer).run()
at.radio(key=f"{prefix}:reason").set_value(situation.reason).run()
at.button(key=f"{prefix}:mark").click().run()
complain("choosing mark", at)
banner = " ".join(m.value for m in at.success)
if "2 out of 2" not in banner:
    problems.append(f"choosing: the right measure with the right reason scored "
                    f"{banner!r}")

at = open_page("choosing")
seed = at.session_state["ct-choose"]["seed"]
situation = choosing.pick(seed)
prefix = f"ct-choose:{situation.key}:{seed}"
wrong_measure = next(m for m in choosing.MEASURES if m != situation.answer)
at.radio(key=f"{prefix}:measure").set_value(wrong_measure).run()
at.radio(key=f"{prefix}:reason").set_value(situation.distractors[0]).run()
at.button(key=f"{prefix}:mark").click().run()
complain("choosing wrong", at)
if not at.error:
    problems.append("choosing: a wrong measure with an uncreditable reason was not "
                    "marked wrong")

at = open_page("choosing")
seed = at.session_state["ct-choose"]["seed"]
situation = choosing.pick(seed)
prefix = f"ct-choose:{situation.key}:{seed}"
at.radio(key=f"{prefix}:measure").set_value(situation.answer).run()
at.button(key=f"{prefix}:mark").click().run()
if not at.warning:
    problems.append("choosing: a measure offered with no reason was marked instead "
                    "of being sent back, though the reason carries its own mark")
print("choosing: both marks for a right answer, none for a wrong one, and a measure "
      "offered without a reason is not marked")

print()
if problems:
    print(f"{len(problems)} PROBLEM(S):")
    for p in problems:
        print("  -", p)
    sys.exit(1)
print("central tendency: the arithmetic matches the notes, no question can tie, "
      "and the notes page reads one measure at a time")
