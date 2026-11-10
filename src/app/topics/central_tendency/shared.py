"""The pieces every page of this topic uses.

Kept apart from the pages themselves because the pages are deliberately
unalike: reading notes, walking a table and answering a marked question want
different layouts, and only the small conversions below are common to all
three.
"""

from typing import Dict, Optional, Sequence

import streamlit as st

from app.core import maths, scoring, ui

from . import engine, generate

TOPIC_LINE = "Unit 5 \u00b7 Measures of central tendency \u00b7 syllabus 4.1"

KIND_NAMES = {
    "list": "From a list of values",
    "table": "From a frequency table",
}

EXAMPLE_CODE = 1204   # the worked examples, so a lesson can refer to them


# ------------------------------------------------------------------- helpers


def as_number(text) -> Optional[float]:
    """A typed answer as a number, or nothing when it cannot be read."""
    try:
        return float(str(text).strip())
    except (TypeError, ValueError):
        return None


def judged(exact: float, given: Optional[float], available: int = 1) -> scoring.Award:
    ok = engine.agrees(exact, given)
    return scoring.Award(marks=available if ok else 0, available=available,
                         errors=0 if ok else 1)


def mean_working(total: int, count: int, value: float) -> str:
    return maths.inline(maths.quotient(total, count, engine.shown(value)))


def position_working(count: int, value: float) -> str:
    return maths.inline(maths.quotient(f"{count} + 1", 2, engine.shown(value)))


def table_markdown(question: Dict,
                   products: Optional[Sequence[Optional[int]]] = None,
                   cumulative: Optional[Sequence[Optional[int]]] = None) -> str:
    """The table, with the two worked columns shown only once they are wanted."""
    rows = generate.rows_of(question)
    head = [question["x_label"] + " (x)", question["f_label"] + " (f)"]
    if products is not None:
        head.append("f × x")
    if cumulative is not None:
        head.append("Running total")
    lines = ["| " + " | ".join(head) + " |",
             "|" + "|".join([" --- "] * len(head)) + "|"]
    for index, row in enumerate(rows):
        cells = [str(row.x), str(row.f)]
        if products is not None:
            value = products[index]
            cells.append("**" + str(value) + "**" if value is not None else "·")
        if cumulative is not None:
            value = cumulative[index]
            cells.append("**" + str(value) + "**" if value is not None else "·")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def show_data(question: Dict) -> None:
    """The question's data, however it is presented."""
    if question["kind"] == "list":
        st.caption(question["label"])
        ui.chips(str(v) for v in question["values"])
    else:
        st.markdown(table_markdown(question))
