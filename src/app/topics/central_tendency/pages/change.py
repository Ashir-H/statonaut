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
        _why_each(question, before)
        return
    after = engine.solve_list(question["after"])
    rows = ["| Measure | Before | After |", "| --- | --- | --- |",
            f"| Mode | {before.mode} | {after.mode} |",
            f"| Median | {engine.shown(before.median)} | "
            f"{engine.shown(after.median)} |",
            f"| Mean | {value_text(before.mean)} | {value_text(after.mean)} |"]
    st.markdown("\n".join(rows))


def _why_each(question: Dict, before) -> None:
    """Why each verdict stands, where the further value is not stated.

    Two of the three can be settled, and a student who answered "not enough
    information" to all of them deserves to be shown which ones were decidable
    and on what grounds.
    """
    values = question["values"]
    lines = []
    if engine.mode_survives_one_more(values):
        lead = engine.modal_lead(values)
        lines.append(f"- The mode stays {before.mode}, which occurs {lead} more "
                     f"times than any other value. One further value adds at most "
                     f"one to a rival, which leaves it short.")
    else:
        lines.append(f"- The mode is in doubt: {before.mode} occurs only one more "
                     f"time than the next commonest value, so a further value could "
                     f"draw level with it and leave no single mode.")
    if engine.median_survives_one_more(values):
        lines.append(f"- The median stays {engine.shown(before.median)}, because "
                     f"the values across the middle are equal. The middle shifts by "
                     f"half a place, but it shifts onto the same value.")
    else:
        lines.append("- The median is in doubt: a value added below the middle "
                     "moves it one way and a value added above it moves it the "
                     "other.")
    lines.append(f"- The mean is in doubt: a value above {value_text(before.mean)} "
                 f"would raise it and a value below would lower it.")
    st.markdown("\n".join(lines))


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
