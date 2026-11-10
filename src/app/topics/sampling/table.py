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


def progress(q, result, read_so_far: int, width: int) -> None:
    """What has been settled, and how far the selection has got.

    Everything needed to rule on the next number, in one place: which numbers
    belong where, how many each stratum still wants, and how many are found.
    Without it the reader has to scroll back to the question for the ranges
    and to an earlier step for the split.
    """
    taken = [s for s in result.steps[:read_so_far] if s.action == ACCEPT]

    if q["kind"] == "stratified":
        rows = []
        for stratum, share in zip(q["strata"], result.shares):
            got = sum(1 for s in taken if s.stratum == stratum.name)
            mark = f"{got} \u2714" if got >= share.count else str(got)
            rows.append(f"| {stratum.name} | {stratum.label_range(width)} "
                        f"| {share.count} | {mark} |")
        st.markdown("| Stratum | Its numbers | Needs | Found |\n|---|---|---:|---:|\n"
                    + "\n".join(rows))
        return

    if q["kind"] == "systematic":
        top = q["lo"] + result.interval - 1
        start = f"{engine.pad(result.start, width)}" if taken else "not yet found"
        st.markdown("| Looking for | Numbers that can be it | Interval |\n"
                    "|---|---|---:|\n"
                    f"| the random start | {engine.pad(q['lo'], width)}\u2013"
                    f"{engine.pad(top, width)} | {result.interval} |\n"
                    f"| found | {start} | |")
        return

    lo, hi = q["lo"], q["hi"]
    got = len(taken)
    mark = f"{got} \u2714" if got >= q["n"] else str(got)
    st.markdown("| The numbers | Needs | Found |\n|---|---:|---:|\n"
                f"| {engine.pad(lo, width)}\u2013{engine.pad(hi, width)} "
                f"| {q['n']} | {mark} |")


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


WIDTHS = (1, 2, 3, 4)


def _width_label(width: int) -> str:
    return "1 digit" if width == 1 else f"{width} digits"


@st.fragment
def regrouper(row: str, key: str, *, labelled: str = "") -> None:
    """Let the reader regroup the table themselves, and watch it happen.

    The table is printed in pairs. Choosing a different block width slides the
    digits into their new blocks and lists the numbers that come out - without
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
    numbers = engine.read_blocks(row, chosen)
    tail = len(digits) - len(numbers) * chosen
    note = f"Reading in blocks of {chosen} gives {len(numbers)} numbers"
    if tail:
        note += f", with {tail} digit{'s' if tail > 1 else ''} left over"
    st.caption(note + (f". {labelled}" if labelled else "."))
    st.markdown(
        motion.sequence(numbers, animation=motion.RISE if moved else None,
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
