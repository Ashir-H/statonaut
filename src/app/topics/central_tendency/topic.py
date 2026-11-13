"""What this topic is, and which pages it has.

The pages are deliberately unalike. A unit earns the kind of page its concepts
need: notes to read and pick through, a walkthrough where the process is what
goes wrong, a drill where fluency is what is missing, and a marked question at
the end. Nothing here follows another unit's shape for the sake of it.
"""

from app.registry import Page, Topic

from .pages import choose, notes, practice, table_walk

TOPIC = Topic(
    key="central-tendency",
    title="The mode, the median and the mean",
    unit="Unit 5",
    unit_title="Measures of central tendency",
    syllabus="4.1 and 4.4",
    summary="The three measures of central tendency: what each one means, how it "
            "is found from a list and from an ungrouped frequency table, and when "
            "each is the right one to use.",
    pages=(
        Page("notes", "The three measures", notes.page_notes,
             ":material/menu_book:",
             "one measure at a time: what it means, how it is computed, "
             "when it is used"),
        Page("walkthrough", "Walk a frequency table",
             table_walk.page_walkthrough, ":material/table_rows:",
             "the fx column and the running total, one cell at a time"),
        Page("choosing", "Choosing a measure", choose.page_choose,
             ":material/balance:",
             "which measure describes the data, and on what grounds"),
        Page("practice", "Practice a question", practice.page_practice,
             ":material/edit:",
             "a whole question from a code, marked part by part"),
    ),
)
