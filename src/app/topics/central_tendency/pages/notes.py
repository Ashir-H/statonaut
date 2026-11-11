"""The notes page: one measure at a time.

A student arriving at this topic is not looking for a wall of text about all
three measures; they are stuck on one of them. So the page shows a single
measure at a time, chosen from a selector, and always in the same four parts:
what it means, how it is computed, when it is used, and how it is marked.

Why each measure is used sits beside that measure rather than in a section of
its own. It is syllabus 4.4, the most examined strand of the topic, and the
reason to reach for the median is the same fact as the mean's weakness, so
separating them would mean saying it twice and teaching it once.
"""

import streamlit as st

from app.core import ui
from app.core.library import ContentError

from .. import content, engine, generate, ordering
from ..shared import (EXAMPLE_CODE, TOPIC_LINE, mean_working, position_working,
                      table_markdown)

CHOICES = {
    "mode": "The mode",
    "median": "The median",
    "mean": "The mean",
}


def page_notes() -> None:
    ui.inject()
    ui.page_header(TOPIC_LINE, "The three measures")

    try:
        st.markdown(content.vocabulary().section(content.WORDS))
    except ContentError as exc:
        st.warning(f"Content needs attention: {exc}")

    chosen = st.segmented_control(
        "Read about", list(CHOICES), format_func=lambda key: CHOICES[key],
        default="mode", key="ct-notes:choice")
    st.divider()
    _measure(chosen or "mode")


def _measure(key: str) -> None:
    try:
        doc = content.measure(key)
    except ContentError as exc:
        st.warning(f"Content needs attention: {exc}")
        return
    st.subheader(doc.title)
    st.markdown(doc.section(content.MEANS))
    st.markdown("### How it is computed")
    st.markdown(doc.section(content.COMPUTED))
    with st.expander("See it done on an example", expanded=True):
        _example(key)
    st.markdown("### When it is used")
    st.markdown(doc.section(content.USED))
    st.markdown("### How it is marked")
    st.markdown(doc.section(content.MARKED))


def _example(key: str) -> None:
    """The same two questions every time, so a lesson can refer to them."""
    list_question = generate.build("list", EXAMPLE_CODE)
    listed = generate.solve(list_question)
    table_question = generate.build("table", EXAMPLE_CODE)
    tabled = generate.solve(table_question)

    st.markdown("**From a list**")
    st.caption(list_question["setting"])
    if key == "mode":
        ui.mono_blocks(
            [(str(v), "acc" if v == listed.mode else "pend") for v in listed.ordered],
            "In ascending order, with the mode picked out")
        st.markdown(
            f"{listed.mode} occurs {list(listed.ordered).count(listed.mode)} times, "
            f"more often than any other value, so the mode is {listed.mode}.")
    elif key == "median":
        st.markdown("Drag these into ascending order, smallest first, then check "
                    "them. The ordering "
                    "is worth a mark on its own, so it is worth being able to do "
                    "it quickly.")
        ordering.ordering_exercise(list_question["values"])
        middle = listed.middle_values
        ending = (f"so the median is {engine.shown(listed.median)}."
                  if len(middle) == 1 else
                  f"which falls between {middle[0]} and {middle[1]}, so the median "
                  f"is {engine.shown(listed.median)}.")
        st.markdown(f"There are {listed.n} values, so the median is the "
                    f"{position_working(listed.n, listed.position)} th value, "
                    + ending)
    else:
        ui.mono_blocks([(str(v), "pend") for v in listed.ordered], "The values")
        st.markdown(
            f"They total {listed.total} and there are {listed.n} of them, so the "
            f"mean is {mean_working(listed.total, listed.n, listed.mean)}.")

    st.markdown("**From a frequency table**")
    st.caption(table_question["setting"])
    if key == "mode":
        st.markdown(table_markdown(table_question))
        st.markdown(
            f"The highest frequency is {max(row.f for row in tabled.rows)}, and the "
            f"value beside it is {tabled.mode}, so the mode is {tabled.mode}.")
    elif key == "median":
        st.markdown(table_markdown(table_question, cumulative=list(tabled.running)))
        which = tabled.median_rows
        landed = (f"row {which[0] + 1}" if len(which) == 1
                  else f"rows {which[0] + 1} and {which[1] + 1}")
        st.markdown(
            f"There are {tabled.sigma_f} values, so the median is the "
            f"{position_working(tabled.sigma_f, tabled.position)} th. The running "
            f"total first reaches that at {landed}, so the median is "
            f"{engine.shown(tabled.median)}.")
    else:
        st.markdown(table_markdown(table_question, products=list(tabled.products)))
        # Built outside the f-string: an f-string expression may not contain a
        # backslash before Python 3.12, and these are LaTeX.
        sigma_fx_text = "$\\Sigma fx = " + str(tabled.sigma_fx) + "$"
        sigma_f_text = "$\\Sigma f = " + str(tabled.sigma_f) + "$"
        st.markdown(
            f"Here {sigma_fx_text} and {sigma_f_text}, so the mean is "
            f"{mean_working(tabled.sigma_fx, tabled.sigma_f, tabled.mean)}.")
