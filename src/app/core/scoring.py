"""Asking a question, remembering the outcome, and keeping the score.

The marking itself lives in `app.core.marks`, which has no Streamlit import;
this module adds the parts that draw on screen and hold session state. It
re-exports the marking helpers so a topic only needs one import.
"""

from typing import Any, Dict, Optional, Sequence

import streamlit as st

from .marks import (Award, mark_count, mark_sample, mark_value,  # noqa: F401
                    parse_numbers)

__all__ = ["Award", "mark_sample", "mark_value", "mark_count", "parse_numbers",
           "part", "remember", "recall", "show_outcome",
           "tally_add", "tally_reset", "tally_sidebar"]


# --------------------------------------------------- one attempt at a question


def part(label: str, award: Award, model: str) -> Dict[str, Any]:
    return {"label": label, "marks": award.marks, "available": award.available,
            "model": model}


def remember(prefix: str, signature: str, parts: Sequence[Dict[str, Any]]) -> None:
    """Keep an outcome so it survives the reruns that follow a click."""
    st.session_state[f"{prefix}:outcome"] = {"sig": signature, "parts": list(parts)}
    tally_add(sum(p["marks"] for p in parts), sum(p["available"] for p in parts))


def recall(prefix: str, signature: str) -> Optional[Dict[str, Any]]:
    """The outcome for this question, or nothing if the question has changed."""
    found = st.session_state.get(f"{prefix}:outcome")
    if found is None:
        return None
    if found["sig"] != signature:
        st.session_state.pop(f"{prefix}:outcome", None)
        return None
    return found


def show_outcome(parts: Sequence[Dict[str, Any]]) -> int:
    """The banner and the part-by-part breakdown. Returns the marks scored."""
    got = sum(p["marks"] for p in parts)
    total = sum(p["available"] for p in parts)
    if got == total:
        st.success(f"**{got} out of {total}.** All correct.")
    elif got == 0:
        st.error(f"**{got} out of {total}.** Work through the answer below, then try another.")
    else:
        st.warning(f"**{got} out of {total}.**")
    for p in parts:
        verdict = ("correct" if p["marks"] == p["available"]
                   else "part marks" if p["marks"] else "not right")
        st.markdown(f"- **{p['label']}** - {p['marks']}/{p['available']}, {verdict}. "
                    f"Answer: `{p['model']}`")
    return got


# ------------------------------------------------------------------- the score


def _tally() -> Dict[str, int]:
    return st.session_state.setdefault("tally", {"marks": 0, "available": 0, "questions": 0})


def tally_add(marks: int, available: int) -> None:
    t = _tally()
    t["marks"] += marks
    t["available"] += available
    t["questions"] += 1


def tally_reset() -> None:
    st.session_state["tally"] = {"marks": 0, "available": 0, "questions": 0}


def tally_sidebar() -> None:
    t = _tally()
    st.sidebar.divider()
    st.sidebar.caption("This session")
    if t["questions"] == 0:
        st.sidebar.write("No questions marked yet.")
        return
    pct = round(100 * t["marks"] / t["available"]) if t["available"] else 0
    st.sidebar.metric(f"{t['questions']} question(s)",
                      f"{t['marks']} / {t['available']}", f"{pct}%")
    if st.sidebar.button("Clear my score", use_container_width=True):
        tally_reset()
        st.rerun()
