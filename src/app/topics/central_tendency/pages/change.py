"""What an alteration to the data does to each measure.

Asked the way the papers ask it: increases, decreases, no change, or not enough
information, judged separately for each of the three measures.

The fourth option is not decoration. Where an alteration is described without
stating the value involved, no verdict about any measure can be given, and an
answer offered regardless has misread the question.

Every verdict shown here is computed from the data before and after the
alteration. A rule of thumb would be quicker and would eventually mark a
correct answer wrong, because whether the median moves when one value is added
depends on the values themselves.
"""

from typing import Dict

import streamlit as st

from app.core import scoring, ui

from .. import engine, generate
from ..shared import TOPIC_LINE, value_text

MEASURES = ("mode", "median", "mean")

NAMES = {"mode": "The mode", "median": "The median", "mean": "The mean"}

SHOWN = {
    engine.INCREASES: "Increases",
    engine.DECREASES: "Decreases",
    engine.UNCHANGED: "No change",
    engine.UNKNOWN: "Not enough information",
}


def _award(correct: bool) -> scoring.Award:
    return scoring.Award(marks=1 if correct else 0, available=1,
                         errors=0 if correct else 1)


def page_change() -> None:
    ui.inject()
    ui.page_header(TOPIC_LINE, "The effect of a change",
                   "What happens to each measure when the data is altered.")
    _, seed = ui.code_controls("ct-change", generate.new_seed)
    _question(generate.build("change", seed), seed)
    st.caption("Share the code to give someone the same question.")


def _before_and_after(question: Dict) -> None:
    """The three measures on each side, once the answer has been marked."""
    before = engine.solve_list(question["values"])
    if not question["told"]:
        st.caption("The size of the further value is not stated, so no measure can "
                   "be said to rise, fall or hold. Before the change the mode is "
                   f"{before.mode}, the median is {engine.shown(before.median)} and "
                   f"the mean is {value_text(before.mean)}.")
        return
    after = engine.solve_list(question["after"])
    rows = ["| Measure | Before | After |", "| --- | --- | --- |",
            f"| Mode | {before.mode} | {after.mode} |",
            f"| Median | {engine.shown(before.median)} | "
            f"{engine.shown(after.median)} |",
            f"| Mean | {value_text(before.mean)} | {value_text(after.mean)} |"]
    st.markdown("\n".join(rows))


def _question(question: Dict, seed: int) -> None:
    prefix = f"ct-change:{seed}"
    signature = f"change:{seed}"
    answers = generate.verdicts(question)

    ui.scenario(question["setting"],
                "State the effect of the change on each measure of central "
                "tendency.")
    st.caption(question["label"])
    ui.chips(str(value) for value in question["values"])
    st.markdown(f"**{question['change']}**")

    remembered = scoring.recall(prefix, signature)
    if remembered:
        scoring.show_outcome(remembered["parts"])
        _before_and_after(question)
        return

    columns = st.columns(3)
    given = {}
    for column, measure in zip(columns, MEASURES):
        given[measure] = column.radio(
            NAMES[measure], list(engine.VERDICTS), index=None,
            format_func=lambda verdict: SHOWN[verdict],
            key=f"{prefix}:{measure}")

    if not st.button("Mark my answer", key=f"{prefix}:mark", type="primary"):
        return
    if any(value is None for value in given.values()):
        st.warning("Answer for all three measures, then mark the answer.")
        return

    parts = [scoring.part(NAMES[measure],
                          _award(given[measure] == answers[measure]),
                          SHOWN[answers[measure]])
             for measure in MEASURES]
    scoring.remember(prefix, signature, parts)
    st.rerun()
