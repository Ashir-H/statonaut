"""Where this topic's words come from.

Nothing here is text. Every sentence a student reads lives in
`content/central-tendency/` as Markdown, so the wording can be corrected
without touching code. This module is the one place that names those files and
the headings the pages rely on.

The files are organised by measure rather than by where the data came from,
because that is how a student arrives at the topic: stuck on the median, not
stuck on tables. Each measure's file therefore covers both a list and a table
inside its own "how it is computed" section.
"""

from typing import List

from app.core.library import ContentError, Document, Library

LIBRARY = Library("central-tendency")

MEASURES = ("mode", "median", "mean")
CLOSING = "closing"

# A measure's file is split on these four headings. Change a heading in a file
# and it must change here too; everything else in the file is free text.
MEANS = "what-it-means"
COMPUTED = "how-it-is-computed"
USED = "when-it-is-used"
MARKED = "how-it-is-marked"

MEASURE_SECTIONS = (MEANS, COMPUTED, USED, MARKED)

WORDS = "the-words-we-use"
RANGE = "the-range"
LATER = "what-comes-later"

CLOSING_SECTIONS = (WORDS, RANGE, LATER)


def text(name: str) -> str:
    """One whole Markdown file."""
    return LIBRARY.text(name)


def measure(name: str) -> Document:
    """One measure's file, split into its sections. The title is its `#` heading."""
    return LIBRARY.document(name)


def closing() -> Document:
    """The vocabulary note, the range, and what comes later."""
    return LIBRARY.document(CLOSING)


def check() -> List[str]:
    """Every complaint about the content files, for the tests and a quick look."""
    trouble: List[str] = []
    wanted = [(name, MEASURE_SECTIONS) for name in MEASURES]
    wanted.append((CLOSING, CLOSING_SECTIONS))
    for name, sections in wanted:
        try:
            doc = LIBRARY.document(name)
        except ContentError as exc:
            trouble.append(str(exc))
            continue
        if not doc.title:
            trouble.append(f"{name}.md has no '# ' title line")
        for section in sections:
            if not doc.has(section):
                trouble.append(
                    f"{name}.md is missing the section '{section}' "
                    f"(it has: {', '.join(doc.bodies) or 'none'})")
            elif not doc.section(section).strip():
                trouble.append(f"{name}.md has an empty '{section}' section")
    return trouble
