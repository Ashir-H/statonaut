"""Single short questions against a new table each time.

The walkthrough beside this page teaches the process; this page is for speed
once the process is understood. One quantity is asked for, the answer is
marked, and the next table is different. Nothing is walked through and nothing
is gated.

The count of right and wrong answers is kept on this page rather than added to
the figure in the sidebar. That figure is a record of marked questions, and a
page of twenty-second drills would swamp it.
"""

import random
from typing import Dict, Tuple

import streamlit as st

from app.core import ui

from .. import engine, generate
from ..shared import SIGMA_F, SIGMA_FX, TOPIC_LINE, as_number, table_markdown

ASKS = ("sigma_f", "sigma_fx", "mean", "position", "median", "mode")


def prompt(ask: str) -> str:
    return {
        "sigma_f": f"Find {SIGMA_F}.",
        "sigma_fx": f"Find {SIGMA_FX}.",
        "mean": "Find the mean. If it does not come out exactly, give it to three "
                "significant figures or two decimal places.",
        "position": "State the position at which the median lies.",
        "median": "Find the median.",
        "mode": "Find the mode.",
    }[ask]


def wanted(ask: str, answers) -> float:
    return {
        "sigma_f": float(answers.sigma_f),
        "sigma_fx": float(answers.sigma_fx),
        "mean": answers.mean,
        "position": answers.position,
        "median": answers.median,
        "mode": float(answers.mode),
    }[ask]


def note(ask: str, answers) -> str:
    """One line on where the answer comes from, shown once it is marked."""
    rows = answers.rows
    if ask == "sigma_f":
        return "The frequency column totals the number of values altogether."
    if ask == "sigma_fx":
        return ("Each value is multiplied by its frequency and the products are "
                "added.")
    if ask == "mean":
        return (f"{engine.shown(answers.sigma_fx)} divided by "
                f"{answers.sigma_f}.")
    if ask == "position":
        return (f"There are {answers.sigma_f} values, so the median lies at the "
                f"({answers.sigma_f} + 1) divided by 2.")
    if ask == "median":
        which = answers.median_rows
        where = (f"row {which[0] + 1}" if len(which) == 1
                 else f"rows {which[0] + 1} and {which[1] + 1}")
        return (f"The running total first reaches position "
                f"{engine.shown(answers.position)} at {where}.")
    return (f"The highest frequency is {max(row.f for row in rows)}, and the value "
            f"beside it is {answers.mode}.")


def ask_for(seed: int) -> str:
    return random.Random(seed * 23 + 9).choice(ASKS)


def _fresh() -> Dict:
    return {"seed": generate.new_seed(), "answered": None,
            "right": 0, "wrong": 0}


def page_quick() -> None:
    ui.inject()
    ui.page_header(TOPIC_LINE, "Quick table questions",
                   "One short question at a time, against a new table each time.")

    state = st.session_state.setdefault("ct-quick", _fresh())
    seed = state["seed"]
    question = generate.build("table", seed)
    answers = generate.solve(question)
    ask = ask_for(seed)

    st.caption(question["setting"])
    st.markdown(table_markdown(question))
    st.markdown(f"**{prompt(ask)}**")

    if state["answered"] is None:
        typed = st.text_input("Answer", key=f"ct-quick:{seed}",
                              label_visibility="collapsed",
                              placeholder="Type a number")
        if st.button("Check", key=f"ct-quick:check:{seed}", type="primary"):
            given = as_number(typed)
            if given is None:
                st.error("Type a number first.")
            else:
                correct = engine.agrees(wanted(ask, answers), given)
                state["answered"] = correct
                state["right" if correct else "wrong"] += 1
                st.rerun()
    else:
        if state["answered"]:
            st.success(f"Correct. {note(ask, answers)}")
        else:
            st.error(f"The answer is {engine.shown(wanted(ask, answers))}. "
                     f"{note(ask, answers)}")
        if st.button("Next question", key=f"ct-quick:next:{seed}", type="primary"):
            state["seed"] = generate.new_seed()
            state["answered"] = None
            st.rerun()

    st.caption(f"{state['right']} right, {state['wrong']} wrong on this page. "
               f"Code {seed}.")
    if st.button("Start the count again", key="ct-quick:reset"):
        st.session_state["ct-quick"] = _fresh()
        st.rerun()
