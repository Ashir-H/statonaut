"""Where this topic's words and questions come from.

Nothing here is text. Every sentence a student reads lives in
`content/sampling/` as Markdown, so wording can be corrected without touching
code. This module is the one place that names those files and the
headings the pages rely on.
"""

from typing import Dict, List

from app.core.library import ContentError, Document, Library

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

def text(name: str) -> str:
    """One whole Markdown file."""
    return LIBRARY.text(name)


def method(kind: str) -> Document:
    """A method's file, split into its sections. The title is its `#` heading."""
    return LIBRARY.document(f"method-{kind}")


def method_section(kind: str, section: str) -> str:
    """One section of one method's file."""
    return method(kind).section(section)


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
    return trouble
