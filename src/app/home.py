"""The front page: what is here, and how to use it."""

import streamlit as st

from . import registry
from .core import ui


def render() -> None:
    ui.inject()
    st.title("Statonaut")
    st.caption("Practice for Cambridge IGCSE Statistics 0479")

    st.markdown(
        "Pick a topic in the sidebar. Each one teaches the method, drills it step "
        "by step, then sets whole questions and marks them the way the papers do."
    )

    st.subheader("Topics")
    for topic in registry.topics():
        rows = "".join(
            f"<li><b>{p.title}</b> - {p.blurb}</li>" for p in topic.pages if p.blurb)
        ui.card(topic.title, topic.line,
                f"<p>{topic.summary}</p><ul style='margin:.3rem 0 0;'>{rows}</ul>")

    st.subheader("Question codes")
    st.markdown(
        "Every generated question has a four-digit code, shown next to it. The code "
        "is the question: type the same code on another computer and you get the same "
        "numbers."
    )

    st.subheader("How answers are marked")
    st.markdown(
        "Marks follow the published schemes rather than a tick for the final answer: "
        "part marks for a sample with one number wrong, a mark of its own for an "
        "interval or a proportion that is written down, and a model answer underneath "
        "that shows every step."
    )
