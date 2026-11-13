"""Questions that give a measure and ask for something else.

The method mark in a question of this kind is for forming the relationship, not
for the arithmetic that follows it, so the relationship is asked for first and
marked separately. A student who reaches the right number by a route the mark
scheme does not recognise has not answered the question that was set.

The four relationships are shown as a lettered list in markdown and selected by
letter, rather than being offered as the labels of a widget. Streamlit strips
unsupported markdown from a widget label, and these are mathematics.
"""

from typing import Dict

import streamlit as st

from app.core import maths, scoring, ui

from .. import engine, generate
from ..shared import TOPIC_LINE, as_number

LETTERS = ("A", "B", "C", "D")


def _award(correct: bool) -> scoring.Award:
    return scoring.Award(marks=1 if correct else 0, available=1,
                         errors=0 if correct else 1)


def page_backwards() -> None:
    ui.inject()
    ui.page_header(TOPIC_LINE, "Working backwards",
                   "A measure is given, and something else is asked for.")
    _, seed = ui.code_controls("ct-back", generate.new_seed)
    _question(generate.build("backwards", seed), seed)
    st.caption("Share the code to give someone the same question.")


def _table(question: Dict) -> None:
    hidden = question["hidden"]
    rows = ["| Goals (x) | Matches (f) |", "| --- | --- |"]
    for index, (value, frequency) in enumerate(question["rows"]):
        rows.append(f"| {value} | {'k' if index == hidden else frequency} |")
    st.markdown("\n".join(rows))


def _question(question: Dict, seed: int) -> None:
    prefix = f"ct-back:{seed}"
    signature = f"{question['shape']}:{seed}"
    unit = question.get("unit", "")
    model = f"{engine.shown(question['answer'])} {unit}".strip()

    ui.scenario(question["setting"], question["task"])
    if "rows" in question:
        _table(question)

    remembered = scoring.recall(prefix, signature)
    if remembered:
        scoring.show_outcome(remembered["parts"])
        return

    st.markdown("**Which equation is needed to find the answer?**")
    st.markdown("\n".join(
        f"- **{letter}** — {maths.inline(option)}"
        for letter, option in zip(LETTERS, question["options"])))
    letter = st.radio("Equation", LETTERS, index=None, horizontal=True,
                      key=f"{prefix}:relation")
    typed = st.text_input("Answer", key=f"{prefix}:answer",
                          placeholder="Type a number")

    if not st.button("Mark my answer", key=f"{prefix}:mark", type="primary"):
        return
    if letter is None or as_number(typed) is None:
        st.warning("Select an equation and give an answer, then mark it.")
        return

    chosen = question["options"][LETTERS.index(letter)]
    parts = [
        scoring.part("Equation", _award(chosen == question["relation"]),
                     maths.inline(question["relation"]), maths=True),
        scoring.part("Answer",
                     _award(engine.agrees(question["answer"], as_number(typed))),
                     model),
    ]
    scoring.remember(prefix, signature, parts)
    st.rerun()
