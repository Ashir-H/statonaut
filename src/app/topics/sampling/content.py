"""Where this topic's words and questions come from.

Nothing here is text. Every sentence a student reads lives in
`content/sampling/` as Markdown, and the questions live in
`content/sampling/questions.toml`, so wording can be corrected without
touching code. This module is the one place that names those files and the
headings the pages rely on.
"""

from typing import Dict, List

from app.core.library import ContentError, Document, Library

from .engine import Stratum

LIBRARY = Library("sampling")

# The pages that are whole files, rendered as they are.
READING = "reading"
REPRESENTATIVE = "representative"
EXAM_NOTES = "exam-notes"
MISTAKES = "mistakes"
INTERVAL_MARKS = "interval-marks"

PAGES = (READING, REPRESENTATIVE, EXAM_NOTES, MISTAKES, INTERVAL_MARKS)

# A method file is split on these headings. Change the heading in the file and
# you must change it here too; everything else in the file is free text.
IDEA = "the-idea"
METHOD = "the-method"
WATCH = "where-marks-are-lost"
MARKS = "how-it-is-marked"

METHOD_SECTIONS = (IDEA, METHOD, WATCH, MARKS)
METHOD_KINDS = ("simple", "systematic", "stratified")

QUESTION_KEYS = ("id", "source", "kind", "setting", "task", "n", "row", "marks")


def text(name: str) -> str:
    """One whole Markdown file."""
    return LIBRARY.text(name)


def method(kind: str) -> Document:
    """A method's file, split into its sections. The title is its `#` heading."""
    return LIBRARY.document(f"method-{kind}")


def method_section(kind: str, section: str) -> str:
    """One section of one method's file."""
    return method(kind).section(section)


def questions() -> List[Dict]:
    """The question bank, read from questions.toml."""
    raw = LIBRARY.data("questions").get("question", [])
    if not raw:
        raise ContentError("questions.toml has no [[question]] entries.")
    bank: List[Dict] = []
    for position, item in enumerate(raw, start=1):
        q = dict(item)
        missing = [k for k in QUESTION_KEYS if k not in q]
        if missing:
            raise ContentError(
                f"Question {position} in questions.toml "
                f"({q.get('id', 'no id')}) is missing: {', '.join(missing)}."
            )
        if q["kind"] == "stratified":
            if "strata" not in q:
                raise ContentError(
                    f"Question {q['id']} is stratified, so it needs a `strata` list.")
            q["strata"] = [Stratum(s["name"], s["lo"], s["hi"]) for s in q["strata"]]
        elif "lo" not in q or "hi" not in q:
            raise ContentError(
                f"Question {q['id']} needs `lo` and `hi`, the lowest and highest label.")
        bank.append(q)
    return bank


def question(question_id: str) -> Dict:
    found = next((q for q in questions() if q["id"] == question_id), None)
    if found is None:
        raise ContentError(f"questions.toml has no question with id '{question_id}'.")
    return found


def of_kind(kind: str) -> List[Dict]:
    return [q for q in questions() if q["kind"] == kind]


def check() -> List[str]:
    """Every complaint about the content files, for the tests and a quick look."""
    trouble: List[str] = []
    for name in PAGES:
        try:
            if not text(name):
                trouble.append(f"{name}.md is empty")
        except ContentError as exc:
            trouble.append(str(exc))
    for kind in METHOD_KINDS:
        try:
            doc = method(kind)
        except ContentError as exc:
            trouble.append(str(exc))
            continue
        if not doc.title:
            trouble.append(f"method-{kind}.md has no '# ' title line")
        for section in METHOD_SECTIONS:
            if not doc.has(section):
                trouble.append(
                    f"method-{kind}.md is missing the section '{section}' "
                    f"(it has: {', '.join(doc.bodies) or 'none'})")
    try:
        bank = questions()
    except ContentError as exc:
        trouble.append(str(exc))
        return trouble
    ids = [q["id"] for q in bank]
    for duplicate in {i for i in ids if ids.count(i) > 1}:
        trouble.append(f"questions.toml uses the id '{duplicate}' more than once")
    for kind in METHOD_KINDS:
        if not of_kind(kind):
            trouble.append(f"questions.toml has no {kind} question to use as an example")
    return trouble
