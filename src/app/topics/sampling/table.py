"""Drawing a random number table, coloured by what happened to each number."""

from typing import Dict, Optional, Sequence

import streamlit as st

from app.core import ui

from . import engine
from .engine import ACCEPT, REJECT, SKIP, Step

CLASS_FOR = {ACCEPT: "acc", REJECT: "rej", SKIP: "skp"}

# The swatches match the block fills, which are translucent so that they sit
# correctly on a light or a dark page.
LEGEND = [("selected", "rgba(34,197,94,.55)"), ("rejected", "rgba(239,68,68,.5)"),
          ("skipped, group full", "rgba(245,158,11,.55)"),
          ("not reached", "rgba(128,128,128,.25)")]

VERDICT = {
    engine.R_IN_RANGE: "selected",
    engine.R_OUT_OF_RANGE: "rejected, outside the numbered range",
    engine.R_REPEAT: "rejected, already selected",
    engine.R_GROUP_FULL: "skipped, that group is already full",
    engine.R_OVER_INTERVAL: "rejected, larger than the interval",
}


def printed_row(row: str, caption: str = "The table as printed, in pairs") -> None:
    ui.printed(engine.in_pairs(row), caption)


def blocks(row: str, width: int, steps: Sequence[Step] = (),
           revealed: Optional[int] = None, current: Optional[int] = None) -> None:
    """The same digits regrouped into reading blocks."""
    by_index: Dict[int, Step] = {s.index: s for s in steps}
    shown = len(steps) if revealed is None else revealed
    drawn = []
    for i, block in enumerate(engine.read_blocks(row, width)):
        if current is not None and i == current:
            cls = "cur"
        elif i < shown and i in by_index:
            cls = CLASS_FOR[by_index[i].action]
        else:
            cls = "pend"
        drawn.append((block, cls))
    ui.mono_blocks(drawn, f"The same digits, read in blocks of {width}")


def legend() -> None:
    ui.legend(LEGEND)


def sample_chips(values: Sequence[int], width: int) -> None:
    ui.chips(engine.pad_all(values, width))


def walkthrough(result, row: str, read_width: int) -> None:
    """The model answer: every block, in order, with the reason for each."""
    blocks(row, read_width, result.steps)
    legend()
    rows = []
    for s in result.steps:
        where = f" ({s.stratum})" if s.stratum and s.action == ACCEPT else ""
        rows.append(f"| `{s.block}` | {VERDICT[s.reason]}{where} |")
    st.markdown("| Number read | What happens to it |\n|---|---|\n" + "\n".join(rows))
