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


def gathering(result, strata) -> None:
    """The selected numbers moving from reading order into their groups.

    One pass along the table gives them in the order they were met; the method
    then wants them grouped. Same values, rearranged - and the rearrangement
    is the part worth seeing.
    """
    tint = {}
    for position, stratum in enumerate(strata):
        for value in result.picks[stratum.name]:
            tint[value] = motion.GROUPS[position % len(motion.GROUPS)]
    order = [result.sample.index(value) for stratum in strata
             for value in result.picks[stratum.name]]
    labels = engine.pad_all(result.sample, result.width)
    st.caption("Read along the table in this order, then gathered into groups:")
    st.markdown(
        motion.reorder(labels, order,
                       item_classes=[tint[v] for v in result.sample], step=0.03),
        unsafe_allow_html=True)
    ui.legend([(s.name, motion.GROUP_COLOURS[i % len(motion.GROUP_COLOURS)])
               for i, s in enumerate(strata)])


WIDTHS = (1, 2, 3, 4)


def _width_label(width: int) -> str:
    return "1 digit" if width == 1 else f"{width} digits"


@st.fragment
def regrouper(row: str, key: str, *, labelled: str = "") -> None:
    """Let the reader regroup the table themselves, and watch it happen.

    The table is printed in pairs. Choosing a different block width slides the
    digits into their new groups and lists the numbers that come out - without
    saying whether that width is the right one for this question. Deciding
    that is the thing being learnt.

    A fragment, so changing the width redraws this and nothing else: no
    content files re-read, no answer box rebuilt, no page scrolled.
    """
    digits = engine.digits(row)
    remembered = st.session_state.setdefault("regroup", {})
    was = remembered.get(key, 2)

    chosen = st.segmented_control(
        "Read the table in blocks of", list(WIDTHS), default=was,
        format_func=_width_label, key=f"regroup:{key}",
        help="The table is printed in pairs. That is how it is printed, not "
             "necessarily how this question needs it read.")
    if chosen is None:
        chosen = was
    remembered[key] = chosen
    moved = chosen != was

    st.markdown(motion.regroup(digits, was, chosen), unsafe_allow_html=True)
    blocks = engine.read_blocks(row, chosen)
    tail = len(digits) - len(blocks) * chosen
    note = f"Reading in blocks of {chosen} gives {len(blocks)} numbers"
    if tail:
        note += f", with {tail} digit{'s' if tail > 1 else ''} left over"
    st.caption(note + (f". {labelled}" if labelled else "."))
    st.markdown(
        motion.sequence(blocks, animation=motion.RISE if moved else None,
                        wrapper_class="chips"),
        unsafe_allow_html=True)


def walkthrough(result, row: str, read_width: int) -> None:
    """The model answer: every block, in order, with the reason for each."""
    blocks(row, read_width, result.steps)
    legend()
    rows = []
    for s in result.steps:
        where = f" ({s.stratum})" if s.stratum and s.action == ACCEPT else ""
        rows.append(f"| `{s.block}` | {VERDICT[s.reason]}{where} |")
    st.markdown("| Number read | What happens to it |\n|---|---|\n" + "\n".join(rows))
