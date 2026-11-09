# Content

Everything a student reads is in this folder, as Markdown. Edit it in any text
editor, save, then reload the page in the browser (press **R**, or click
Rerun). No Python involved, and nothing to restart.

Markdown works as you would expect: `**bold**`, `*italic*`, `` `code` ``,
bullet and numbered lists, tables, and `>` for a quotation. Headings inside a
file show up as headings on the page.

## content/sampling/ — random number tables

| File | Where it appears |
|---|---|
| `reading.md` | "How it is done", the first tab |
| `method-simple.md` | the Simple random tab |
| `method-systematic.md` | the Systematic tab |
| `method-stratified.md` | the Stratified tab |
| `representative.md` | the Representative? tab, and the mark-scheme note on that question |
| `exam-notes.md` | the In the exam tab |
| `mistakes.md` | the list at the foot of the In the exam tab |
| `interval-marks.md` | the mark-scheme note on the "smallest possible sample size" question |
| `questions.toml` | the questions on "Questions from our own papers" |

### The four method files have headings the app looks for

Change the words under a heading as much as you like. Keep the headings
themselves, because the page puts them in different places — the method and the
warnings sit side by side in two columns:

```markdown
# Simple random sample      <- the tab's heading

## The idea
## The method
## Where marks are lost
## How it is marked
```

The `#` title line is the heading shown above the tab's content. If a heading
goes missing, the page says so in place, naming the file — it does not break.

### questions.toml

Each `[[question]]` is one question. The wording is yours to change; the
numbers decide the answer, and the app works the answer out for itself rather
than storing one.

```toml
[[question]]
id = "ws-1"                     # must be unique
source = "..."                  # shown under the question
kind = "simple"                 # simple | systematic | stratified
setting = "..."                 # the situation
task = "..."                    # what the student has to do
lo = 1                          # lowest label in the population
hi = 48                         # highest label
n = 6                           # sample size asked for
marks = 3                       # what the selection is worth
row = "63 17 42 90 05 ..."      # the table, printed in pairs
note = "..."                    # optional, shown with the mark scheme
```

A stratified question has `strata` instead of `lo` and `hi`:

```toml
strata = [
    { name = "Junior", lo = 1, hi = 30 },
    { name = "Senior", lo = 31, hi = 50 },
    { name = "Veteran", lo = 51, hi = 60 },
]
```

Adding a question needs no code: copy a block, change the values, give it a new
`id`. `tests/test_content.py` checks that every question can actually be
completed from the row it is given, and that the twelve already set in class
still produce the answers printed on those papers.
