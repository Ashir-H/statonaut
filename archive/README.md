# Archive

Material kept for reference, not loaded by the app.

## sampling-questions.toml

The twelve random number table questions set in class — the Unit 1 deck
examples, the random number tables worksheet and the CA1 retake — each with
its wording, its numbers and the source it came from.

They were shown in the app as a "From our papers" page. That page was removed
so the app suits any class rather than one, but the questions are still
checked by `tests/test_content.py`: it confirms every one can be completed
from the row it is given and still produces the answer printed on that paper.

To put them back, read this file with `app.core.library` and register a page
that walks the list, as `views.page_bank` used to.
