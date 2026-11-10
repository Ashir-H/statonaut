# Statonaut

A practice app for **Cambridge IGCSE Statistics 0479**. Each topic teaches the
method, drills it step by step, then sets whole questions and marks them the way
the papers do.

Topics live side by side in the sidebar, so the app grows with the course. The
first one is **Unit 1 · Random number tables** (syllabus 1.2 and 1.4).

## Running it

```bash
uv sync
uv run streamlit run streamlit_app.py
```

Start it through uv, or activate the project's `.venv` first. A bare
`streamlit run` uses whichever Streamlit is first on PATH, which may be an
older one installed system-wide — and the sidebar navigation needs 1.40 or
newer. Without uv:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

It opens at <http://localhost:8501>. Every page also has its own address, so a
lesson plan can link straight to one: `/sampling_drill`, `/sampling_practice`.

## What is here

**Home** — what the app is, the topics, how question codes work.

**Unit 1 · Random number tables**

| Page | What it is for |
|---|---|
| How it is done | The reading rule, then a tab per method: the steps, where marks are lost, how it is marked, and a worked example from our own papers. |
| Selecting step by step | The drill. One number at a time, the student decides select / reject / skip and is told why, in the syllabus's own words. Every decision is scored. |
| Practice a question | A whole question, generated from a four-digit code, with Cambridge-style marking and a number-by-number model answer. Five types, including "smallest possible sample size" and "is this sample representative?". |
| From our papers | The twelve questions already set in class: the Unit 1 deck examples, the random number tables worksheet, and the CA1 retake. |

Codes make questions reproducible: put **code 4821** on the board and every
student gets the same table.

## How it is built

```
content/                      everything a student reads, as Markdown
content/sampling/             one folder per topic
archive/                      material kept for reference, not loaded
streamlit_app.py              router: builds the sidebar from the registry
src/app/registry.py           Topic and Page, and the list of topics
src/app/home.py               the front page, written from the registry
src/app/core/ui.py            stylesheet and the pieces every topic reuses
src/app/core/library.py       finds and splits the content files
src/app/core/motion.py        the animation primitives, CSS only
src/app/core/marks.py         marking, with no Streamlit import: testable alone
src/app/core/scoring.py       outcomes on screen and the running score
src/app/topics/sampling/      one topic: topic, engine, generate, content, table, views
tests/test_sampling_engine.py the engine against every answer checked in class
tests/test_content.py         the content files, and the answers they still give
tests/test_app.py             every registered page rendered and answered
```

`core/` knows nothing about any topic: it holds the stylesheet, the monospace
block renderer, and the ask-mark-show-the-answer plumbing (`mark_sample`,
`mark_value`, `mark_count`, `remember`, `show_outcome`, the session tally).
A topic supplies its own questions and input forms. `core/marks.py` imports
nothing from Streamlit, so marking and any topic's own logic can be tested
without it installed.

### Changing the words

No page has its text in the code. Edit the Markdown in `content/`, save, and
reload the page in the browser — see [content/README.md](content/README.md) for
which file is which. Questions are generated, so there is no
question list to maintain.

If a file or a heading the page looks for goes missing, the page says so in
place, naming the file, and carries on.

### Adding a topic

1. Make `src/app/topics/<name>/` with the content, the question generation, and
   a `views.py` of page functions.
2. In its `topic.py`, expose a `TOPIC = Topic(...)` listing its pages. Leave
   `__init__.py` empty, so the topic's own logic imports without Streamlit.
3. Add one line to `registry.topics()`.

The sidebar, the home page and `tests/test_app.py` all read the registry, so a
new topic appears in the navigation and is covered by the tests with no further
edits.

### The sidebar

`st.navigation` takes a mapping of section heading to pages, which gives two
levels: **topic**, then **page**. That is what the app uses — one section per
topic, headed `Unit 1 · Random number tables`.

Worth knowing before going deeper:

- Sidebar sections are headings, not collapsible items. Collapsible groups
  exist only for `position="top"`.
- `expanded=True` keeps the whole menu open; by default it truncates with a
  "View more" button past twelve pages. At four pages a topic, that is three
  topics before truncation starts, so revisit this then.
- URL pathnames cannot be nested (Streamlit issue #8971), so addresses join the
  two levels with an underscore: `sampling_drill`.
- For a third level (unit → topic → page), `st.navigation` accepts a different
  page set on every rerun, so a unit picker in the sidebar can filter the
  sections it is given. `registry.Topic` already carries `unit`, so that is a
  change to the router alone.

## Animation

Streamlit redraws a block's HTML on every interaction, so no DOM node survives
from one state to the next. Two rules follow, and they decide the approach:

**Animation is CSS, and the browser's compositor does the work.** A Python loop
over `st.empty()` with `time.sleep` is a server round trip per frame: it blocks
the script, and with a class of students it serialises. Nothing in
`core/motion.py` sleeps or reruns.

**Keyframes for something that appeared; a transition for something that
changed.** This is the rule that matters, and getting it wrong cost four rounds
of fruitless tuning. Streamlit does *not* replace a markdown block's elements
on a rerun — React patches attributes on the elements it already has. A
finished keyframe animation does not re-run when that happens; it only holds a
new end value, so the thing jumps in a single frame. Proved in the running app:
after a click the digit's animation still reported the same `startTime`, state
`finished`, on the same DOM node, while its position changed instantly.

So anything that must move when a **value changes** — the digits regrouping —
declares its resting position in its own style and transitions to it. The patch
*is* the trigger, and no element identity is relied on. Keyframes stay for
things that genuinely mount fresh: a sample arriving, a stratified gathering
revealed inside an expander.

**The resting layout must never depend on an animation.** Because the digit
offsets used to be the end state of a keyframe, `prefers-reduced-motion` took
the gaps away along with the motion. Now the offset is the element's own style,
so reduced motion removes only the transition: the grouping is still visible,
it simply arrives without sliding.

Only `transform` and `opacity` are ever animated; both are composited off the
main thread, while width, height, top or margin would force a layout on every
frame. `tests/test_app.py` reads the keyframes and fails on anything else.
Everything stops for `prefers-reduced-motion`.

### Making a movement perceptible

Measured in Chrome: every duration, travel distance and cascade tried held
60fps with **no late frame**, and still did at 200 animated elements. So
rendering is not the constraint. What matters is **speed and distance**, and
the first attempt here got that wrong — a digit crossing one block gap
travelled 6.7px, and stretching that over a longer duration only made it read
as more stationary. Slow is not the same as smooth.

What the dials actually are, in `core/motion.py`:

| | | |
|---|---|---|
| `IDEAL_GAP` | `1.15` rem | how far a digit travels per block it crosses — the real lever |
| `REGROUP_SECONDS` | `0.52` | short enough to keep the speed up |
| `STAGGER_BUDGET` | `0.3` | the whole left-to-right cascade, not per block |
| `STAGGER_MAX` | `0.055` | never a longer pause than this between two blocks |

Measured in the running app: a digit crosses 49px over 20 distinct positions
on the same element, which is a real interpolation rather than a jump. Across
row lengths a digit moves a median of 24–69px at **46–133 px/second**, against
roughly 20px/s where motion stops registering. Movement begins about 200ms
after the click — the Streamlit round trip — which is unavoidable and fine.
The cascade has a budget rather than a per-block delay, so a long table does
not take proportionally longer than a short one.

The gap cannot simply be large, because the row has to stay inside the
column — a table whose end scrolls out of sight hides the digits that move
most. So `motion.fit()` solves for the type size and gap from the character
count and the number of blocks, sized for the animation's **widest moment**:
going from pairs to threes, the row is widest at the very start, since pairs
make more blocks. The cell widths it works from were measured in Chrome at
each type size. `tests/test_app.py` recomputes that arithmetic and fails if a
row would be clipped, or if its digits would move slower than 25px/s.

The primitives:

| | |
|---|---|
| `motion.regroup(chars, was, now)` | the same sequence gathered into blocks of a new width — the digits of a table sliding from pairs into threes |
| `motion.reorder(labels, order)` | one row of items moving to a new order, each sliding from where it was — unused for now, kept for sorting a list (finding a median) |
| `motion.sequence(labels)` | items arriving one after another, where the order is the point |
| `motion.one(label)` | a single thing, for the one that just changed |

Where they are used: the reader picks the block width on any table question and
watches the digits regroup, rather than being told which width the question
wants; a stratified sample arrives in the order it was read, each member coloured by its stratum; a sample
arrives in the order it was selected; and in the drill, exactly two blocks are
animated per click — the one just decided, and the one to decide next.

Interactive animation goes inside `st.fragment`, so changing the block width
redraws that region alone and leaves the answer box and the rest of the page
untouched.

Two things deliberately not used: `components.v1.html`, which would buy
JavaScript at the cost of an iframe that cannot inherit the page's colours, and
is only worth it for something like drag and drop; and any animation of a
Streamlit-managed element such as `st.dataframe`, which React owns.

## Tests

```bash
python tests/test_sampling_engine.py
python tests/test_content.py
python tests/test_app.py
```

The first is 42 checks, each an answer already verified in the class materials:
the Unit 1 deck, the random number tables worksheet, the CA1 retake, the 0479
2027 specimen paper 2, and 4040 November 2023 and 2024. If a change breaks one
of them, the engine is wrong.

The second reads every content file, checks the headings the pages rely on are
present, and confirms the twelve questions in `questions.toml` still produce
the answers printed on those papers — so a mistyped row is caught rather than
quietly changing an answer.

The third builds the navigation, checks every page address is legal and unique,
renders every registered page, completes a drill for each method, submits a
correct and an incorrect answer for every question type, and marks all twelve
bank questions.

Nothing in the app is a stored answer. A question is built from its code, then
solved by the same engine the student is marked against, so a question and its
answer cannot drift apart.
