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

### Questions

Every question in the app is generated from a four-digit code, so there is no
list of questions to keep up to date. The twelve set in class are kept in
`archive/sampling-questions.toml`, which the app does not read; see the README
there.
