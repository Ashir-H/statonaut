"""A whole question, asked and marked the way the papers do it.

Five answers rather than three. The mark schemes pay separately for the working
- ordering the data, the f x column, the position of the median - so asking
only for the three measures would let a student score full marks for bare
numbers that no examiner would accept.
"""

from typing import Dict

import streamlit as st

from app.core import scoring, ui

from .. import engine, generate, ordering
from ..shared import (KIND_NAMES, ROUNDING, TOPIC_LINE, as_number, judged,
                      mean_working, position_working, show_data)


# -------------------------------------------------------------- the question


def attempt(question: Dict, prefix: str) -> None:
    """One whole question, asked and marked the way the papers do it."""
    answers = generate.solve(question)
    signature = generate.signature(question)
    from_table = question["kind"] == "table"
    count = answers.sigma_f if from_table else answers.n
    total = answers.sigma_fx if from_table else answers.total
    total_label = "Σfx" if from_table else "Σx"

    ui.scenario(question["setting"],
                "Find the mode, the median and the mean. Show the working the "
                "mark scheme asks for. " + ROUNDING)
    show_data(question)

    remembered = scoring.recall(prefix, signature)
    if remembered:
        scoring.show_outcome(remembered["parts"])
        return

    # Rough work for a list, in place of rewriting the values on paper. It
    # cannot check anything and it cannot name the median: the median and its
    # position are two of the five marks on this page.
    if question["kind"] == "list":
        st.caption("Rough work: drag the values into ascending order.")
        ordering.ordering_exercise(question["values"], mode=ordering.WORKING)

    left, right = st.columns(2)
    mode_in = left.text_input("Mode", key=f"{prefix}:mode")
    position_in = left.text_input("The median is at which position?",
                                  key=f"{prefix}:position")
    median_in = left.text_input("Median", key=f"{prefix}:median")
    total_in = right.text_input(total_label, key=f"{prefix}:total")
    mean_in = right.text_input("Mean", key=f"{prefix}:mean")

    if not st.button("Mark my answer", key=f"{prefix}:mark", type="primary"):
        return

    typed = [mode_in, position_in, median_in, total_in, mean_in]
    if any(as_number(t) is None for t in typed):
        st.warning("Fill in every box, then mark it.")
        return

    parts = [
        scoring.part("Mode", judged(answers.mode, as_number(mode_in)),
                     str(answers.mode)),
        scoring.part("Median position",
                     judged(answers.position, as_number(position_in)),
                     position_working(count, answers.position), maths=True),
        scoring.part("Median", judged(answers.median, as_number(median_in)),
                     engine.shown(answers.median)),
        scoring.part(total_label, judged(total, as_number(total_in)), str(total)),
        scoring.part("Mean", judged(answers.mean, as_number(mean_in)),
                     mean_working(total, count, answers.mean), maths=True),
    ]
    scoring.remember(prefix, signature, parts)
    st.rerun()


def page_practice() -> None:
    ui.inject()
    ui.page_header(TOPIC_LINE, "Practice a whole question",
                   "Written and marked the way the papers do it.")
    kind, seed = ui.code_controls("ct-practice", generate.new_seed,
                                  options=list(KIND_NAMES),
                                  format_func=lambda k: KIND_NAMES[k])
    attempt(generate.build(kind, seed), prefix=f"ct-practice:{kind}:{seed}")
    st.caption("Share the code to give someone the same question.")
