"""Selecting a measure of central tendency, and justifying the selection.

The page asks for both at once, as the papers do: a measure, and a reason that
refers to the data rather than to the measure in general. The reason is the
harder half, so the statements offered against it are not nonsense. Each is
either true of the measure but silent about this particular data, or it
confuses one measure with another.

The situations themselves live in content/central-tendency/choosing.toml.
"""

import streamlit as st

from app.core import scoring, ui
from app.core.library import ContentError

from .. import choosing, content, engine, generate
from ..shared import TOPIC_LINE, value_text


def _award(correct: bool) -> scoring.Award:
    return scoring.Award(marks=1 if correct else 0, available=1,
                         errors=0 if correct else 1)


def page_choose() -> None:
    ui.inject()
    ui.page_header(TOPIC_LINE, "Choosing a measure",
                   "Which measure describes the data, and on what grounds.")

    with st.expander("What a question of this kind requires"):
        _prose()

    _, seed = ui.code_controls("ct-choose", generate.new_seed)
    try:
        situation = choosing.pick(seed)
    except ContentError as exc:
        st.warning(f"Content needs attention: {exc}")
        return
    _question(situation, seed)
    st.caption("Share the code to give someone the same question.")


def _prose() -> None:
    try:
        doc = content.choosing()
    except ContentError as exc:
        st.warning(f"Content needs attention: {exc}")
        return
    st.markdown(doc.section(content.REQUIRES))
    st.markdown("### What makes a reason creditable")
    st.markdown(doc.section(content.CREDITABLE))
    st.markdown("### When each measure is preferred")
    st.markdown(doc.section(content.PREFERRED))
    st.markdown("### Where marks are lost")
    st.markdown(doc.section(content.LOST))


def _data(situation: choosing.Situation) -> None:
    if situation.numerical:
        st.caption(situation.label)
        ui.chips(str(value) for value in situation.values)
        return
    rows = [f"| {situation.label} | Frequency |", "| --- | --- |"]
    rows += [f"| {name} | {count} |"
             for name, count in zip(situation.categories, situation.frequencies)]
    st.markdown("\n".join(rows))


def _question(situation: choosing.Situation, seed: int) -> None:
    prefix = f"ct-choose:{situation.key}:{seed}"
    signature = f"{situation.key}:{seed}"

    ui.scenario(situation.setting,
                "Name the measure of central tendency that best describes this "
                "data, and select the reason that would be credited for it.")
    _data(situation)

    remembered = scoring.recall(prefix, signature)
    if remembered:
        scoring.show_outcome(remembered["parts"])
        if situation.numerical:
            answers = engine.solve_list(situation.values)
            mode = answers.mode if answers.mode is not None else "none"
            st.caption(f"For this data the mode is {mode}, the median is "
                       f"{engine.shown(answers.median)} and the mean is "
                       f"{value_text(answers.mean)}.")
        return

    measure = st.radio("Measure", list(choosing.MEASURES), index=None,
                       format_func=lambda key: choosing.NAMES[key],
                       key=f"{prefix}:measure", horizontal=True)
    reason = st.radio("Reason", situation.statements(seed), index=None,
                      key=f"{prefix}:reason")

    if not st.button("Mark my answer", key=f"{prefix}:mark", type="primary"):
        return
    if measure is None or reason is None:
        st.warning("Select a measure and a reason, then mark the answer.")
        return

    parts = [
        scoring.part("Measure", _award(measure == situation.answer),
                     choosing.NAMES[situation.answer]),
        scoring.part("Reason", _award(reason == situation.reason), situation.reason),
    ]
    scoring.remember(prefix, signature, parts)
    st.rerun()
