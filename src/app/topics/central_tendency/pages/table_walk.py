"""Walking a frequency table, one cell at a time.

This is a walkthrough rather than a drill: one table, every intermediate value
visible, and no way past a cell until it is right. A student who is handed the
mean of a table can reproduce the number without ever building the f x column,
and a student who reads the median off the middle of the x column is right
often enough to believe the method. So the page asks for the column and the two
totals before it asks for the mean, which is also the order the mark scheme
pays for.
"""

from typing import Dict, List

import streamlit as st

from app.core import maths, ui

from .. import engine, generate
from ..shared import (FX, SIGMA_F, SIGMA_FX, TOPIC_LINE, as_number,
                      mean_working, table_markdown, value_text)


# ----------------------------------------------------------------- the drill


def walk_steps(answers) -> List[Dict]:
    """Every question the drill asks, in the order the marks are earned."""
    steps: List[Dict] = []
    for index, row in enumerate(answers.rows):
        steps.append({
            "kind": "fx", "row": index, "want": float(row.fx),
            "ask": f"Row {index + 1}: the value is {row.x} and its frequency is "
                   f"{row.f}. What goes in the {FX} column?",
            "why": "Multiply the value by its frequency. This row stands for "
                   f"{row.f} items each worth {row.x}.",
        })
    steps.append({
        "kind": "sigma_fx", "row": None, "want": float(answers.sigma_fx),
        "ask": f"Add the {FX} column. What is {SIGMA_FX}?",
        "why": "Add the column you have just built, not the x column.",
    })
    steps.append({
        "kind": "sigma_f", "row": None, "want": float(answers.sigma_f),
        "ask": f"Add the frequency column. What is {SIGMA_F}?",
        "why": "This is how many values there are altogether, not how many rows "
               "the table has.",
    })
    steps.append({
        "kind": "mean", "row": None, "want": answers.mean,
        "ask": "Now divide. What is the mean? If it does not come out exactly, "
               "give it to three significant figures or two decimal places.",
        "why": "Divide Σfx by Σf.",
    })
    for index, row in enumerate(answers.rows):
        steps.append({
            "kind": "run", "row": index, "want": float(answers.running[index]),
            "ask": f"Row {index + 1}: what is the running total of the frequencies "
                   f"up to and including this row?",
            "why": "Add this row's frequency to the running total above it.",
        })
    steps.append({
        "kind": "position", "row": None, "want": answers.position,
        "ask": f"There are {answers.sigma_f} values. Which position does the median "
               f"sit at?",
        "why": "The median is the (n + 1) ÷ 2 th value.",
    })
    steps.append({
        "kind": "median", "row": None, "want": answers.median,
        "ask": "Count down the running total to that position. What is the median?",
        "why": "Find the first running total that reaches the position, then give "
               "the value on that row - not the running total itself.",
    })
    return steps


def fresh_state(signature: str, rows: int) -> Dict:
    return {"sig": signature, "step": 0, "right": 0, "wrong": 0, "last": None,
            "fx": [None] * rows, "run": [None] * rows,
            "sigma_fx": None, "sigma_f": None, "mean": None,
            "position": None, "median": None}


def page_walkthrough() -> None:
    ui.inject()
    ui.page_header(TOPIC_LINE, "Walk a frequency table",
                   "The fx column, then the totals, then the running total "
                   "and the median.")
    _, seed = ui.code_controls("ct-walk", generate.new_seed)
    question = generate.build("table", seed)
    answers = generate.solve(question)
    steps = walk_steps(answers)
    signature = generate.signature(question)

    state = st.session_state.setdefault("ct-walk:state", {})
    if state.get("sig") != signature:
        state = fresh_state(signature, len(answers.rows))
        st.session_state["ct-walk:state"] = state

    st.caption(question["setting"])
    done = state["step"]
    show_products = any(step["kind"] == "fx" for step in steps[:done]) or done > 0
    show_running = any(step["kind"] == "run" for step in steps[:done])
    st.markdown(table_markdown(
        question,
        state["fx"] if show_products else None,
        state["run"] if show_running else None,
    ))

    if state["sigma_fx"] is not None or state["sigma_f"] is not None:
        bits = []
        if state["sigma_fx"] is not None:
            bits.append(r"\Sigma fx = " + str(int(state["sigma_fx"])))
        if state["sigma_f"] is not None:
            bits.append(r"\Sigma f = " + str(int(state["sigma_f"])))
        st.markdown(maths.joined(bits, "  ·  "))
    if state["mean"] is not None:
        st.markdown("**Mean** " + mean_working(answers.sigma_fx, answers.sigma_f,
                                               answers.mean))

    if state["step"] >= len(steps):
        st.success("The table is complete.")
        st.markdown(
            f"- Mode {answers.mode}\n"
            f"- Median {value_text(answers.median)}\n"
            f"- Mean {value_text(answers.mean)}"
        )
        st.caption(f"{state['right']} right, {state['wrong']} wrong along the way.")
        if st.button("Start this table again"):
            st.session_state["ct-walk:state"] = fresh_state(signature,
                                                             len(answers.rows))
            st.rerun()
        return

    step = steps[state["step"]]
    st.progress(state["step"] / len(steps),
                text=f"Step {state['step'] + 1} of {len(steps)}")
    st.markdown("**" + step["ask"] + "**")
    typed = st.text_input("Your answer", key=f"ct-walk:{signature}:{state['step']}",
                          label_visibility="collapsed", placeholder="Type a number")
    if st.button("Check", key=f"ct-walk:check:{state['step']}"):
        given = as_number(typed)
        if given is None:
            state["last"] = (False, "Type a number first.")
        elif engine.agrees(step["want"], given):
            if step["kind"] in ("fx", "run"):
                state[step["kind"]][step["row"]] = int(step["want"])
            else:
                state[step["kind"]] = step["want"]
            state["step"] += 1
            state["right"] += 1
            state["last"] = (True, "")
            st.rerun()
        else:
            state["wrong"] += 1
            state["last"] = (False, step["why"])

    if state["last"]:
        ok, message = state["last"]
        if not ok:
            st.error("Not that. " + message)
