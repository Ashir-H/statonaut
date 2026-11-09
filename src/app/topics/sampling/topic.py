"""What this topic is, and which pages it has."""

from app.registry import Page, Topic

from . import views

TOPIC = Topic(
    key="sampling",
    title="Random number tables",
    unit="Unit 1",
    unit_title="Data and its collection",
    syllabus="1.2 and 1.4",
    summary="Simple random, systematic and stratified samples selected from a "
            "random number table, plus the two questions that come with them: the "
            "smallest possible sample size, and whether a sample is representative.",
    pages=(
        Page("learn", "How it is done", views.page_learn, ":material/school:",
             "the reading rule, then a tab for each method with a worked example"),
        Page("drill", "Walk the table", views.page_drill, ":material/arrow_forward:",
             "one number at a time: select, reject or skip, and why"),
        Page("practice", "Practice a question", views.page_practice, ":material/edit:",
             "a whole question from a code, marked part by part"),
        Page("papers", "From our papers", views.page_bank, ":material/description:",
             "the twelve already set in class, answers already checked"),
    ),
)
