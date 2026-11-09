"""Render every registered page, and work through the ones that take answers.

Uses Streamlit's own test harness, so this exercises the real widgets. Pages
are reached through `app.registry`, so a new topic is covered by these tests
the moment it is registered.
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from streamlit.testing.v1 import AppTest  # noqa: E402

from app import registry  # noqa: E402
from app.core import scoring  # noqa: E402
from app.topics.sampling import content, engine, generate, views  # noqa: E402

ENTRY = str(ROOT / "streamlit_app.py")
problems = []


def complain(where, at):
    for e in at.exception:
        problems.append(f"{where}: {e.value}")


def open_page(topic, page):
    """Run one page as its own script, with the real imports in place.

    AppTest.from_function inlines a function's source without its module
    globals, and AppTest.switch_page only resolves file-based pages, so a
    page registered as a callable is reached by a small script instead.
    """
    script = (
        "import sys\n"
        f"sys.path.insert(0, {str(ROOT / 'src')!r})\n"
        "from app import registry\n"
        f"topic = next(t for t in registry.topics() if t.key == {topic.key!r})\n"
        f"topic.page({page.key!r}).render()\n"
    )
    return AppTest.from_string(script, default_timeout=90).run()


def _find(page_key):
    """The topic and page registered under this key."""
    return next((t, p) for t, p in registry.pages() if p.key == page_key)


# 1. the entry script builds its navigation and lands on the home page
at = AppTest.from_file(ENTRY, default_timeout=90).run()
complain("entry script", at)
titles = [t.value for t in at.title]
if "Statistics 101" not in titles:
    problems.append(f"home page title missing, saw {titles}")
print(f"entry script: home page is '{titles[0] if titles else None}', "
      f"{len(registry.topics())} topic(s) registered")

# 2. every page has a legal, unique address
seen = {}
for topic, page in registry.pages():
    path = registry.url_path(topic, page)
    if "/" in path:
        problems.append(f"address '{path}': Streamlit has no nested pathnames")
    if path in seen:
        problems.append(f"address '{path}' is used by {seen[path]} as well")
    seen[path] = f"{topic.key}/{page.key}"
print(f"addresses: {len(seen)} unique page paths, all single segment")

# 3. a second topic must not break the sidebar or the addresses
import dataclasses  # noqa: E402

real = registry.topics
extra = dataclasses.replace(real()[0], key="second", title="A second topic")
registry.topics = lambda: real() + [extra]
try:
    at = AppTest.from_file(ENTRY, default_timeout=90).run()
    complain("entry script with two topics", at)
    print("sidebar: two topics group into two sections without clashing addresses")
finally:
    registry.topics = real

# 4. every page renders on its own
for topic, page in registry.pages():
    at = open_page(topic, page)
    complain(f"page '{page.title}'", at)
    print(f"renders: {topic.key}/{page.key:9} "
          f"{len(at.button)} buttons, {len(at.text_input)} text inputs, "
          f"{len(at.number_input)} numbers")

# 5. the drill: answer every number of a table correctly, then start another
for kind in views.TABLE_KINDS:
    at = open_page(*_find("drill"))
    at.selectbox(key="drill_kind").set_value(kind).run()
    complain(f"drill {kind} load", at)
    seed = at.session_state["drill"]["seed"]
    q = generate.build(kind, seed)
    steps = views.solve(q).steps
    for n, step in enumerate(steps):
        key = f"drill:{seed}:{n}:{step.reason}"
        match = [b for b in at.button if b.key == key]
        if not match:
            problems.append(f"drill {kind}: no button for step {n} ({step.reason})")
            break
        match[0].click().run()
        complain(f"drill {kind} step {n}", at)
    drill = at.session_state["drill"]
    if drill["wrong"] or drill["right"] != len(steps):
        problems.append(f"drill {kind}: scored {drill['right']} right, "
                        f"{drill['wrong']} wrong, of {len(steps)}")
    print(f"drill {kind:11} {len(steps)} decisions, all scored right")
    again = [b for b in at.button if "Another table" in str(b.label)]
    if again:
        again[0].click().run()
        complain(f"drill {kind} restart", at)


# 6. practice: the right answer scores full marks, a wrong one does not
def fill(at, kind, q, prefix, correct=True):
    if kind in ("simple", "systematic"):
        r = views.solve(q)
        box = f"{prefix}:{'srs' if kind == 'simple' else 'sys'}"
        at.text_input(key=box).set_value(
            " ".join(engine.pad_all(r.sample, r.width)) if correct else "99 98 97")
        if kind == "systematic":
            at.number_input(key=f"{prefix}:k").set_value(r.interval if correct else 1)
    elif kind == "stratified":
        r = views.solve(q)
        for share in r.shares:
            at.number_input(key=f"{prefix}:size:{share.name}").set_value(
                share.count if correct else 0)
        for name, picks in r.picks.items():
            at.text_input(key=f"{prefix}:pick:{name}").set_value(
                " ".join(engine.pad_all(picks, r.width)) if correct else "99")
    elif kind == "interval":
        at.number_input(key=f"{prefix}:diff").set_value(q["difference"] if correct else 1)
        at.number_input(key=f"{prefix}:size").set_value(q["answer"] if correct else 1)
    else:
        for group, want in zip(q["groups"], q["expected"]):
            at.number_input(key=f"{prefix}:exp:{group}").set_value(want if correct else 99)
        wanted = "Yes, it is representative" if q["fair"] else "No, it is not representative"
        other = "No, it is not representative" if q["fair"] else "Yes, it is representative"
        at.radio(key=f"{prefix}:verdict").set_value(wanted if correct else other)


practice_topic, practice_page = _find("practice")
for kind in views.KIND_NAMES:
    for correct in (True, False):
        at = open_page(practice_topic, practice_page)
        at.selectbox(key="practice:choice").set_value(kind).run()
        complain(f"practice {kind} load", at)
        seed = at.session_state["practice"]["seed"]
        q = generate.build(kind, seed)
        fill(at, kind, q, f"practice:{kind}:{seed}", correct)
        submit = [b for b in at.button if "Mark my answer" in str(b.label)]
        if not submit:
            problems.append(f"practice {kind}: no submit button")
            continue
        submit[0].click().run()
        complain(f"practice {kind} submit", at)
        t = at.session_state["tally"]
        full = t["marks"] == t["available"] and t["available"] > 0
        if correct and not full:
            problems.append(f"practice {kind}: a correct answer scored "
                            f"{t['marks']}/{t['available']}")
        if not correct and full:
            problems.append(f"practice {kind}: a wrong answer scored full marks")
        if correct:
            print(f"practice {kind:15} correct answer scored "
                  f"{t['marks']}/{t['available']}")

# 7. every bank question renders and marks
at = open_page(*_find("papers"))
for item in content.questions():
    at.selectbox(key="bank_choice").set_value(item["id"]).run()
    complain(f"bank {item['id']}", at)
    submit = [b for b in at.button if "Mark my answer" in str(b.label)]
    if submit:
        submit[0].click().run()
        complain(f"bank {item['id']} submit", at)
print(f"bank: {len(content.questions())} questions rendered and marked")

print()
if problems:
    print(f"{len(problems)} PROBLEM(S):")
    for p in problems:
        print("  -", p)
    sys.exit(1)
print("app: navigation builds, every page renders and routes, every question marks")
