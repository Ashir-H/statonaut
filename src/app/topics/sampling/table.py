"""Drawing a random number table, coloured by what happened to each number."""

from typing import Dict, Optional, Sequence

import streamlit as st

from app.core import motion, ui

from . import engine
from .engine import ACCEPT, REJECT, SKIP, Step

CLASS_FOR = {ACCEPT: "acc", REJECT: "rej", SKIP: "skp"}

# The swatches match the block fills, which are translucent so that they sit
# correctly on a light or a dark page.
LEGEND = [("selected", "rgba(34,197,94,.55)"), ("rejected", "rgba(239,68,68,.5)"),
          ("skipped, group fully sampled", "rgba(245,158,11,.55)"),
          ("not reached", "rgba(128,128,128,.25)")]

VERDICT = {
    engine.R_IN_RANGE: "selected",
    engine.R_OUT_OF_RANGE: "rejected, not in the sampling frame",
    engine.R_REPEAT: "rejected, already selected",
    engine.R_GROUP_FULL: "skipped, that group is fully sampled",
    engine.R_OVER_INTERVAL: "rejected, greater than the sampling interval",
}


def printed_row(row: str, caption: str = "The table as printed, in pairs") -> None:
    ui.printed(engine.in_pairs(row), caption)


def blocks(row: str, width: int, steps: Sequence[Step] = (),
           revealed: Optional[int] = None, current: Optional[int] = None,
           just: Optional[int] = None) -> None:
    """The same digits regrouped into reading blocks.

    Only two blocks are ever animated: the one just decided, and the one to
    decide next. Animating the whole row on every click would redraw forty
    elements to show one change.
    """
    by_index: Dict[int, Step] = {s.index: s for s in steps}
    shown = len(steps) if revealed is None else revealed
    drawn = []
    for i, block in enumerate(engine.read_blocks(row, width)):
        animation = None
        if current is not None and i == current:
            cls = "cur"
            animation = motion.PULSE
        elif i < shown and i in by_index:
            cls = CLASS_FOR[by_index[i].action]
            if i == just:
                animation = motion.POP
        else:
            cls = "pend"
        drawn.append((block, motion.classes(animation, cls)))
    ui.mono_blocks(drawn, f"The same digits, read in blocks of {width}")


def legend() -> None:
    ui.legend(LEGEND)


def sample_chips(values: Sequence[int], width: int, *, animate: bool = True) -> None:
    """The sample, arriving in the order it was selected."""
    labels = engine.pad_all(values, width)
    if not animate:
        ui.chips(labels)
        return
    st.markdown(motion.sequence(labels, wrapper_class="chips"),
                unsafe_allow_html=True)


def coloured_sample(result, strata) -> None:
    """The sample in the order the numbers came off the table.

    Not regrouped: the mark schemes list a stratified sample in the order it
    was read, so that is the order shown. Which stratum each member belongs to
    is carried by its colour, which says the same thing without rearranging
    the answer a student has to write down.
    """
    tint = {}
    for position, stratum in enumerate(strata):
        for value in result.picks[stratum.name]:
            tint[value] = motion.GROUPS[position % len(motion.GROUPS)]
    labels = engine.pad_all(result.sample, result.width)
    st.caption("The sample, in the order the numbers came off the table. The "
               "colours show which stratum each one belongs to.")
    st.markdown(
        motion.sequence(labels, item_classes=[tint[v] for v in result.sample],
                        wrapper_class="chips"),
        unsafe_allow_html=True)
    ui.legend([(s.name, motion.GROUP_COLOURS[i % len(motion.GROUP_COLOURS)])
               for i, s in enumerate(strata)])


def walkthrough(result, row: str, read_width: int) -> None:
    """The model answer: every block, in order, with the reason for each."""
    blocks(row, read_width, result.steps)
    legend()
    rows = []
    for s in result.steps:
        where = f" ({s.stratum})" if s.stratum and s.action == ACCEPT else ""
        rows.append(f"| `{s.block}` | {VERDICT[s.reason]}{where} |")
    st.markdown("| Number read | What happens to it |\n|---|---|\n" + "\n".join(rows))
