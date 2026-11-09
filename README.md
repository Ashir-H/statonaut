# Statistics 101

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
| Walk the table | The drill. One number at a time, the student decides select / reject / skip and is told why. Every decision is scored. |
| Practice a question | A whole question, generated from a four-digit code, with Cambridge-style marking and a number-by-number model answer. Five types, including "smallest possible sample size" and "is this sample representative?". |
| From our papers | The twelve questions already set in class: the Unit 1 deck examples, the random number tables worksheet, and the CA1 retake. |

Codes make questions reproducible: put **code 4821** on the board and every
student gets the same table.

## How it is built

```
content/                      everything a student reads, as Markdown
content/sampling/             one folder per topic, plus questions.toml
streamlit_app.py              router: builds the sidebar from the registry
src/app/registry.py           Topic and Page, and the list of topics
src/app/home.py               the front page, written from the registry
src/app/core/ui.py            stylesheet and the pieces every topic reuses
src/app/core/library.py       finds and splits the content files
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
which file is which. Questions live in `content/sampling/questions.toml`, and
adding one needs no code either.

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
