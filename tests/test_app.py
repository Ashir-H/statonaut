"""Render every registered page, and work through the ones that take answers.

Uses Streamlit's own test harness, so this exercises the real widgets. Pages
are reached through `app.registry`, so a new topic is covered by these tests
the moment it is registered.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from streamlit.testing.v1 import AppTest  # noqa: E402

from app import form, registry  # noqa: E402
from app.core import scoring  # noqa: E402
from app.topics.sampling import engine, generate, views  # noqa: E402

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


def _find(page_key, topic_key="sampling"):
    """The topic and page registered under this key.

    The topic has to be named. Page keys repeat across topics - every topic has
    a "drill" - so a bare search would quietly return whichever topic happens
    to be registered first.
    """
    return next((t, p) for t, p in registry.pages()
                if p.key == page_key and t.key == topic_key)


# 1. the entry script builds its navigation and lands on the home page
at = AppTest.from_file(ENTRY, default_timeout=90).run()
complain("entry script", at)
titles = [t.value for t in at.title]
if "Statonaut" not in titles:
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
for extra in registry.standalone():
    if "/" in extra.key:
        problems.append(f"address '{extra.key}': Streamlit has no nested pathnames")
    if extra.key in seen:
        problems.append(f"address '{extra.key}' is used by {seen[extra.key]} as well")
    seen[extra.key] = f"standalone/{extra.key}"
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


# 4b. a page belonging to no topic still has to render, and this one is a frame
# around somebody else's page, so it also has to cope with that page not
# arriving
def open_standalone(key):
    script = (
        "import sys\n"
        f"sys.path.insert(0, {str(ROOT / 'src')!r})\n"
        "from app import registry\n"
        f"page = next(p for p in registry.standalone() if p.key == {key!r})\n"
        "page.render()\n"
    )
    return AppTest.from_string(script, default_timeout=90).run()


for extra in registry.standalone():
    at = open_standalone(extra.key)
    complain(f"standalone page '{extra.title}'", at)
    if not at.header:
        problems.append(f"'{extra.title}' has no heading of its own, so it opens on "
                        f"somebody else's form with nothing to say what it is")
    print(f"renders: {extra.key} under '{extra.section}'")

# Streamlit cannot measure a page from another origin, so a height of "content"
# silently becomes 400px, which cuts this four-field form in half.
if not isinstance(form.HEIGHT, int):
    problems.append("the feedback frame states no height, so Streamlit falls back "
                    "to 400px and cuts the form off")
for url in (form.EMBED, form.DIRECT):
    if not url.startswith("https://"):
        problems.append(f"the feedback form is reached over plain http: {url}")
at = open_standalone("submit-feedback")
said = " ".join(c.value for c in at.caption)
if form.DIRECT not in said:
    problems.append("the feedback page offers no way through if the frame does not "
                    "load, which a school network blocking the domain would cause")
if "optional" not in said.lower():
    problems.append("the feedback page does not say the e-mail box is optional, "
                    "though it asks a student for an address")
print(f"feedback: {form.HEIGHT}px stated, https, a link out if the frame fails, "
      "and the e-mail box declared optional")

# 5. the drill: answer every number of a table correctly, then start another
for kind in views.TABLE_KINDS:
    at = open_page(*_find("drill"))
    at.selectbox(key="drill_kind").set_value(kind).run()
    complain(f"drill {kind} load", at)
    seed = at.session_state["drill"]["seed"]
    q0 = generate.build(kind, seed)
    solved0 = views.solve(q0)
    if kind == "stratified":
        # the split has to be worked out before anything else happens
        want = [sh.count for sh in solved0.shares]
        for stratum, count in zip(q0["strata"], want):
            at.number_input(key=f"split:{seed}:{stratum.name}").set_value(count + 1)
        [b for b in at.button if "Check" in str(b.label)][0].click().run()
        complain(f"drill {kind} wrong split", at)
        if at.session_state["drill"]["stage"] != "split":
            problems.append(f"drill {kind}: a wrong split let the student through")
        for stratum, count in zip(q0["strata"], want):
            at.number_input(key=f"split:{seed}:{stratum.name}").set_value(count)
        [b for b in at.button if "Check" in str(b.label)][0].click().run()
        [b for b in at.button if "how to read the table" in str(b.label)][0].click().run()
        complain(f"drill {kind} right split", at)
        if at.session_state["drill"]["stage"] != "width":
            problems.append(f"drill {kind}: the right split did not open step two")
    if kind == "systematic":
        # the interval has to be worked out before anything else happens
        at.number_input(key=f"interval:{seed}:value").set_value(solved0.interval + 1)
        [b for b in at.button if "Check" in str(b.label)][0].click().run()
        complain(f"drill {kind} wrong interval", at)
        if at.session_state["drill"]["stage"] != "interval":
            problems.append(f"drill {kind}: a wrong interval let the student through")
        at.number_input(key=f"interval:{seed}:value").set_value(solved0.interval)
        [b for b in at.button if "Check" in str(b.label)][0].click().run()
        [b for b in at.button if "how to read the table" in str(b.label)][0].click().run()
        complain(f"drill {kind} right interval", at)
        if at.session_state["drill"]["stage"] != "width":
            problems.append(f"drill {kind}: the right interval did not open step two")
    # the width has to be ruled on before any number is
    want = views.needed_width(q0, solved0)[0]
    wrong = next(w for w in (1, 2, 3, 4) if w != want)
    [b for b in at.button if b.key == f"width:{seed}:{wrong}"][0].click().run()
    complain(f"drill {kind} wrong width", at)
    if at.session_state["drill"]["stage"] != "width":
        problems.append(f"drill {kind}: a wrong width let the student straight through")
    [b for b in at.button if b.key == f"width:{seed}:{want}"][0].click().run()
    [b for b in at.button if "rule on each number" in str(b.label)][0].click().run()
    complain(f"drill {kind} right width", at)
    if at.session_state["drill"]["stage"] != "numbers":
        problems.append(f"drill {kind}: the right width did not open step two")
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
    opening = {"systematic": "interval, then width",
               "stratified": "split, then width"}.get(kind, "width")
    print(f"drill {kind:11} {opening} ruled on first, then {len(steps)} "
          "decisions, all scored right")
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

# 8. the New question button really draws a new question
practice = _find("practice")
at = open_page(*practice)
seeds = {at.session_state["practice"]["seed"]}
for press in range(4):
    [b for b in at.button if "New question" in str(b.label)][0].click().run()
    complain(f"new question press {press + 1}", at)
    seed = at.session_state["practice"]["seed"]
    code = at.text_input(key="practice:code").value
    if code != str(seed):
        problems.append(f"the code box shows {code} but the question is {seed}")
    seeds.add(seed)
if len(seeds) < 4:
    problems.append(f"five presses of New question gave only {len(seeds)} questions")
at.text_input(key="practice:code").set_value("4821").run()
if at.session_state["practice"]["seed"] != 4821:
    problems.append("typing a code no longer pins the question")
print(f"new question: {len(seeds)} different questions from five presses, "
      "code box follows, typed code still pins")


# 9. the stylesheet has to work on a light and a dark page
from app.core import motion as core_motion  # noqa: E402
from app.core import ui as core_ui  # noqa: E402

STYLESHEET = core_ui.CSS + core_motion.CSS

if re.search(r"@media[^{]*prefers-color-scheme", core_ui.CSS):
    problems.append("the stylesheet switches on the operating system's colour "
                    "scheme, which is wrong whenever that disagrees with the "
                    "app's own theme")


def _luminance(colour):
    def channel(value):
        value /= 255
        return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in colour)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(front, back):
    high, low = sorted((_luminance(front), _luminance(back)), reverse=True)
    return (high + 0.05) / (low + 0.05)


# Streamlit's own light and dark defaults: page colour and body text colour.
THEMES = {"light": ((255, 255, 255), (49, 51, 63)),
          "dark": ((14, 17, 23), (250, 250, 250))}

worst = (99.0, "")
for rule in re.finditer(r"([^{}]+)\{([^}]*)\}", STYLESHEET):
    selector, body = rule.group(1).strip(), rule.group(2)
    fill = re.search(r"background:\s*rgba\(([^)]+)\)", body)
    if not fill:
        if re.search(r"background:\s*#", body):
            problems.append(f"'{selector}' uses an opaque colour fill, which only "
                            "suits one theme")
        continue
    red, green, blue, alpha = (float(v) for v in fill.group(1).split(","))
    for name, (page, text) in THEMES.items():
        behind = tuple(alpha * f + (1 - alpha) * p
                       for f, p in zip((red, green, blue), page))
        score = _contrast(text, behind)
        if score < worst[0]:
            worst = (score, f"'{selector}' on the {name} theme")
        if score < 4.5:
            problems.append(f"'{selector}' leaves text at {score:.1f}:1 on the "
                            f"{name} theme, below the 4.5:1 needed to read it")
print(f"stylesheet: readable on both themes, worst case {worst[0]:.1f}:1 "
      f"at {worst[1]}")

# Streamlit's header is fixed, 60px tall, and paints over whatever is beneath
# it. Its own top padding on the main container clears that; tightening it
# pushed the first line of every page - the unit and syllabus caption - under
# the header and clipped it.
tightened = re.search(r"\.block-container\s*\{[^}]*padding-top:\s*([\d.]+)rem",
                      STYLESHEET)
if tightened and float(tightened.group(1)) < 5:
    problems.append(f"the stylesheet sets the main container's top padding to "
                    f"{tightened.group(1)}rem, which puts the first line of a page "
                    "under Streamlit's 60px fixed header")
print("page top: nothing tightens the main container under Streamlit's header")


# 10. animation has to stay off the main thread and out of the server
COMPOSITED = {"transform", "opacity"}
for frames in re.finditer(r"@keyframes\s+([\w-]+)\s*\{(.+?)\}\s*\n",
                          core_motion.CSS, re.S):
    name, body = frames.group(1), frames.group(2)
    for prop in set(re.findall(r"([a-z-]+)\s*:", body)):
        if prop not in COMPOSITED:
            problems.append(f"@keyframes {name} animates '{prop}', which forces "
                            "layout or paint on every frame; only transform and "
                            "opacity are composited")
if not re.search(r"@media[^{]*prefers-reduced-motion", core_motion.CSS):
    problems.append("the animations ignore prefers-reduced-motion")

# The lesson that cost four rounds of tuning: Streamlit patches attributes on
# elements it already has, rather than inserting new ones. A finished keyframe
# animation does not re-run when that happens, it only holds a new end value,
# so the thing jumps. Anything that has to move when a value *changes* needs a
# transition; keyframes are for something that has just *appeared*.
digit = re.search(r"\.s101-seq \.ch \{([^}]*)\}", core_motion.CSS)
if not digit:
    problems.append("the digit row's own rule has gone, so none of the checks "
                    "below mean anything")
else:
    rule = digit.group(1)
    if "transform:" not in rule:
        problems.append("the digit row's offset is not in its own resting style, so "
                        "the gaps between blocks exist only while something animates")
    if not re.search(r"transition:[^;]*transform", rule):
        problems.append("the digit row has no transition on transform, so a width "
                        "change patched onto the existing elements will jump")
    if "animation-name" in rule or "animation:" in rule:
        problems.append("the digit row's position depends on an animation, which will "
                        "not re-run when Streamlit patches the element in place")
reduced = re.search(r"@media[^{]*prefers-reduced-motion[^{]*\{(.+?)\n\}",
                    core_motion.CSS, re.S)
if reduced and "transition: none" not in reduced.group(1):
    problems.append("prefers-reduced-motion switches off animations but not the "
                    "transition, so the digit row would still slide")
# Read the code, not the prose about it: a docstring may well mention sleep
# in order to explain why there is none.
import ast as _ast  # noqa: E402

for source in sorted((ROOT / "src").rglob("*.py")):
    body = source.read_text(encoding="utf-8")
    tree = _ast.parse(body)
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Call):
            called = node.func
            name = (called.attr if isinstance(called, _ast.Attribute)
                    else getattr(called, "id", ""))
            if name == "sleep":
                problems.append(f"{source.name} calls sleep(), which holds the "
                                "server for every frame of an animation")
    # st.markdown strips a script, so one written into a page's HTML is dead
    # code that only looks as though it works. Inside st.iframe a script does
    # run, so a module that frames its own page is allowed one.
    framed = "st.iframe(" in body
    for text in (n.value for n in _ast.walk(tree)
                 if isinstance(n, _ast.Constant) and isinstance(n.value, str)):
        if "<script" in text and not framed:
            problems.append(f"{source.name} emits a <script> tag into markdown, "
                            "where it is stripped; hand the page to st.iframe "
                            "instead")
frames_found = sorted(re.findall(r"@keyframes\s+([\w-]+)", core_motion.CSS))
print(f"animation: {len(frames_found)} keyframes, all on transform/opacity only, "
      "reduced motion respected, no sleeps and no scripts")

# the regrouping maths: each digit carries the block it now belongs to, and
# nothing about where it came from - the browser interpolates from wherever
# the digit already is, which is what makes the transition work at all
for was, now, expected in ((2, 3, [0, 0, 0, 1, 1, 1]), (3, 2, [0, 0, 1, 1, 2, 2])):
    html = core_motion.regroup("123456", was, now)
    got = [int(m) for m in re.findall(r"--block: (-?\d+)", html)]
    if got != expected:
        problems.append(f"regrouping 6 digits from {was} to {now} put them in "
                        f"blocks {got}, expected {expected}")
    for stale in ("--was", "--now", "--mid"):
        if stale in html:
            problems.append(f"the markup still carries {stale}, left over from the "
                            "keyframe approach that could not re-fire")
print("regrouping: each digit carries only the block it now belongs to")

# the row has to fit the column at its widest moment, or the end of the table
# is clipped exactly as it starts to move
widest = (0.0, "")
for length in (20, 26, 32, 40, 44, 48):
    for was, now in ((2, 1), (2, 3), (2, 4), (3, 2), (4, 2)):
        blocks = max(-(-length // was), -(-length // now))
        font, gap = core_motion.fit(length, blocks)
        cell = dict(core_motion.CELL_PX)[float(font.removesuffix("rem"))]
        used = length * cell + (blocks - 1) * float(gap.removesuffix("rem")) * 16
        # Reading a long table in single digits cannot fit and is allowed to
        # scroll; every grouping a question actually asks for has to fit.
        allowance = core_motion.COLUMN_PX * (1.15 if now == 1 else 1.0)
        if used > allowance:
            problems.append(f"{length} characters read in {now}s needs {used:.0f}px, "
                            f"against a {allowance:.0f}px allowance: the end of the "
                            "table would be clipped as it moves")
        travel = 3 * float(gap.removesuffix("rem")) * 16 / core_motion.REGROUP_SECONDS
        if travel < 25 and now != 1:
            problems.append(f"{length} characters read in {now}s move at only "
                            f"{travel:.0f}px/s, which reads as stationary")
        widest = max(widest, (used, f"{length} characters in blocks of {now}"))
print(f"row width: fits the {core_motion.COLUMN_PX}px column at its widest moment "
      f"({widest[0]:.0f}px, {widest[1]})")



# 11. every question must be answerable from what is on the page
def facts_needed(q):
    """The numbers a student cannot answer this question without."""
    kind = q["kind"]
    if kind == "representative":
        return ([str(v) for v in q["sizes"]] + [str(v) for v in q["observed"]]
                + [str(q["population"]), str(q["n"])] + list(q["groups"]))
    if kind == "interval":
        return [str(q["population"]), str(q["a"]), str(q["b"])]
    if kind == "stratified":
        width = engine.label_width(max(x.hi for x in q["strata"]))
        return ([str(q["n"])] + [x.name for x in q["strata"]]
                + [engine.pad(x.lo, width) for x in q["strata"]])
    width = engine.label_width(q["hi"])
    # the whole table, spelled as it is printed: in pairs
    return [str(q["n"]), engine.pad(q["lo"], width), engine.pad(q["hi"], width),
            engine.in_pairs(q["row"])]


for kind in views.KIND_NAMES:
    q = generate.build(kind, 4821)
    if not views.task_text(q).strip():
        problems.append(f"a {kind} question states no task: the scenario box is "
                        "followed by an empty line")
    at = AppTest.from_string(
        "import sys\n"
        f"sys.path.insert(0, {str(ROOT / 'src')!r})\n"
        "from app.topics.sampling import views, generate\n"
        f"views.attempt(generate.build({kind!r}, 4821), prefix='check')\n",
        default_timeout=90).run()
    complain(f"answerable check, {kind}", at)
    on_page = " ".join(
        [m.value for m in at.markdown] + [c.value for c in at.caption]
        + [str(w.label) for w in at.number_input] + [str(w.label) for w in at.text_input]
        + [str(w.label) for w in at.radio] + [str(o) for w in at.radio for o in w.options]
    )
    missing = [f for f in facts_needed(q) if f not in on_page]
    if missing:
        problems.append(f"a {kind} question cannot be answered from the page: "
                        f"{missing} appear nowhere on it")
print(f"answerable: all {len(views.KIND_NAMES)} question types state their task and "
      "show every number needed to answer")

# 12. mathematics is handed to KaTeX, not printed as text in a code span
from app.core import maths as core_maths  # noqa: E402

sample_share = core_maths.share(36, 240, 40, 6)
if "\\frac" not in sample_share or "\u00d7" in sample_share:
    problems.append(f"a stratum's share is not LaTeX: {sample_share}")
marked = scoring.part("The group sizes", scoring.Award(2, 2),
                      core_maths.inline(sample_share), maths=True)
if not marked.get("maths"):
    problems.append("a model answer holding a formula is not marked as mathematics, "
                    "so it will be shown in a code span and never rendered")
for expression in (core_maths.inline(sample_share),
                   core_maths.joined([sample_share, sample_share], ";  ")):
    if expression.count("$") % 2:
        problems.append(f"unbalanced dollars in {expression}")
    if " $" in expression.replace(";  $", "") or "$ " in expression:
        problems.append(f"a space just inside the dollars stops KaTeX: {expression}")
print("mathematics: formulas are LaTeX, model answers that hold one say so")

print()
if problems:
    print(f"{len(problems)} PROBLEM(S):")
    for p in problems:
        print("  -", p)
    sys.exit(1)
print("app: navigation builds, every page renders and routes, every question marks")
