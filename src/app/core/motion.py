"""Animation that costs the server nothing.

Streamlit re-runs the script and redraws a block's HTML on every interaction,
so there is no DOM node that survives from one state to the next. Two things
follow, and they decide everything here:

* **Animation has to be CSS, declared in the markup, playing on mount.** A
  Python loop over `st.empty()` with `time.sleep` is a server round trip per
  frame: it blocks the script, and with a class of students it serialises.
  Nothing in this module calls `sleep` or `st.rerun`.
* **A move between two states has to be expressed inside one render.** An item
  is drawn where it ends up, offset to where it began, and animated to zero -
  so the finished markup is already correct, and the motion is how it got
  there. This is what `reorder` does.

Only `transform` and `opacity` are ever animated. Both are handled by the
compositor, off the main thread, with no layout or repaint; animating width,
height, top or margin would force a layout on every frame. `tests/test_app.py`
enforces that rule by reading the keyframes below.

Everything stops for anyone who has asked their system for less motion.
"""

from typing import Iterable, Optional, Sequence

GAP = "0.6rem"          # the gap between items in a row, needed by the maths below
STEP = 0.055            # seconds between items in a staggered sequence

# Making a movement slower or larger costs nothing: it is a number in a
# stylesheet, and the browser composites the frames either way. Measured in
# Chrome, a 26-digit table regrouping held 60fps with no late frame at every
# duration, travel distance and stagger tried, and still did at 200 elements.
# What it does cost is the reader's time, so the cascade has a budget: however
# many groups a table falls into, the whole thing is over within
# REGROUP_SECONDS + STAGGER_BUDGET.
# Perceptibility is speed and distance, not duration: the same small movement
# stretched over longer reads as stationary. A digit crossing one block gap
# travels one gap, so the gap is the lever, and the duration stays short
# enough to keep the speed up.
# A wider gap means further travel, but the row has to stay inside the column:
# a table whose end scrolls out of sight hides the digits that move most. So
# the gap is solved for, not fixed - from the number of characters and the
# number of blocks they fall into, which is what reading in ones rather than
# threes changes. Cell widths measured in Chrome at each type size; the column
# is what a centred Streamlit layout gives.
COLUMN_PX = 704
CELL_PX = ((1.3, 16.95), (1.15, 15.44), (1.0, 13.92), (0.9, 12.91),
           (0.8, 11.89))
IDEAL_GAP = 1.15        # rem: as far as a digit ever needs to travel per block
FLOOR_GAP = 0.28        # rem: below this the blocks stop reading as separate
SEQ_LIFT = "0.4rem"     # every digit rises as it goes, so none looks inert
REGROUP_SECONDS = 0.52  # fast enough to read as movement
STAGGER_BUDGET = 0.3    # the whole left-to-right cascade, not per group
STAGGER_MAX = 0.055     # but never a longer pause than this between groups

RISE = "s101-rise"      # fades up into place: for something newly shown
POP = "s101-pop"        # a small overshoot: for the one thing that just happened
SHIFT = "s101-shift"    # slides from where it used to be: for a re-ordering
PULSE = "s101-pulse"    # beats a few times: for the thing to look at next

CSS = """
<style>
/* Only transform and opacity: both composited, neither forces a layout. */
@keyframes s101-rise  {from {opacity: 0; transform: translateY(.4rem);}
                       to   {opacity: 1; transform: none;}}
@keyframes s101-pop   {0%   {opacity: 0; transform: scale(.86);}
                       60%  {opacity: 1; transform: scale(1.05);}
                       100% {opacity: 1; transform: none;}}
@keyframes s101-shift {from {transform: translateX(calc(var(--shift, 0) * (100% + __GAP__)));}
                       to   {transform: none;}}
@keyframes s101-pulse {0%, 100% {transform: none;}
                       50%      {transform: scale(1.07);}}

.s101-anim {animation-duration: .42s; animation-fill-mode: both;
            animation-timing-function: cubic-bezier(.2, .7, .3, 1);}
.s101-rise  {animation-name: s101-rise;}
.s101-pop   {animation-name: s101-pop;}
.s101-shift {animation-name: s101-shift; animation-duration: .55s;}
.s101-pulse {animation-name: s101-pulse; animation-duration: .9s;
             animation-iteration-count: 3; animation-fill-mode: none;}

/* A sequence of single characters, each the same width. */
.s101-seq {font-family: ui-monospace, SFMono-Regular, Menlo,
           Consolas, monospace; line-height: 2.4;
           white-space: nowrap; overflow-x: auto; padding-bottom: .2rem;}
/* The offset that separates the blocks is the element's own resting style,
   not the end state of an animation. Streamlit patches attributes on elements
   it already has rather than inserting new ones, and a finished keyframe
   animation does not re-run when that happens - it just holds a new end
   value, so the digit jumps. A transition fires on the value change itself,
   which is exactly what the patch is. It also means the gaps are there
   whether or not anything is allowed to move. */
.s101-seq .ch {display: inline-block; width: 1.05ch; text-align: center;
               padding: .2rem .12rem; border-radius: .25rem; color: inherit;
               transform: translateX(calc(var(--block, 0) * var(--gap)));
               transition: transform __REGROUP__s cubic-bezier(.2, .7, .3, 1);}
.s101-seq .g0 {background: rgba(128,128,128,.17);}
.s101-seq .g1 {background: rgba(128,128,128,.055);}

/* Items in a reordering row: same width, so a slide of one place is exact. */
.s101-row span {font-family: ui-monospace, SFMono-Regular, Menlo, Consolas,
                monospace; text-align: center; padding: .28rem .2rem;
                border-radius: .4rem; color: inherit; font-weight: 600;
                border: 1px solid rgba(128,128,128,.35);
                background: rgba(128,128,128,.14);}
.s101-row .s101-grp0, .chips .s101-grp0 {background: rgba(59,130,246,.24); border-color: rgba(59,130,246,.55);}
.s101-row .s101-grp1, .chips .s101-grp1 {background: rgba(168,85,247,.24); border-color: rgba(168,85,247,.55);}
.s101-row .s101-grp2, .chips .s101-grp2 {background: rgba(20,184,166,.26); border-color: rgba(20,184,166,.55);}
.s101-row .s101-grp3, .chips .s101-grp3 {background: rgba(234,179,8,.26); border-color: rgba(234,179,8,.55);}

/* A row whose items are all the same width, so a slide of one place is
   exactly one item plus one gap - no measuring, no JavaScript. */
.s101-row {display: grid; gap: __GAP__; align-items: center; margin: .2rem 0 .5rem;}

@media (prefers-reduced-motion: reduce) {
  .s101-anim {animation: none !important;}
  /* The movement goes, the gaps stay: the offset is not the animation. */
  .s101-seq .ch {transition: none !important;}
}
</style>
""".replace("__GAP__", GAP).replace("__REGROUP__", str(REGROUP_SECONDS))


# Tints for telling groups apart in a reordering row, with the same colours
# again as plain values, for a legend beside it.
GROUPS = ("s101-grp0", "s101-grp1", "s101-grp2", "s101-grp3")
GROUP_COLOURS = ("rgba(59,130,246,.55)", "rgba(168,85,247,.55)",
                 "rgba(20,184,166,.6)", "rgba(234,179,8,.6)")


def classes(animation: Optional[str], extra: str = "") -> str:
    """The class attribute for one animated thing."""
    names = [extra] if extra else []
    if animation:
        names += ["s101-anim", animation]
    return " ".join(n for n in names if n)


def _delay(index: int, step: float) -> str:
    return f"animation-delay: {index * step:.3f}s;" if step and index else ""


def sequence(labels: Sequence[str], *, animation: str = RISE, step: float = STEP,
             item_class: str = "", item_classes: Optional[Sequence[str]] = None,
             wrapper_class: str = "") -> str:
    """Items appearing one after another, in the order given.

    Used where the order is itself the point: the members of a sample arrive in
    the order they were selected.
    """
    parts = [
        f"<span class='{classes(animation, item_classes[i] if item_classes else item_class)}' "
        f"style='{_delay(i, step)}'>{label}</span>"
        for i, label in enumerate(labels)
    ]
    return f"<div class='{wrapper_class}'>{''.join(parts)}</div>"


def reorder(labels: Sequence[str], order: Sequence[int], *,
            item_classes: Optional[Sequence[str]] = None,
            step: float = 0.0) -> str:
    """One row of items moving from the order given to a new order.

    `labels` is the row as it stands; `order` holds indices into it, in the
    order they should end up. Each item is drawn in its new place, offset by
    however many places it has moved, and slides to zero.

    A statistics example: the members of a stratified sample are read off the
    table in one order, then gathered into their groups. The same values, a
    different arrangement, and the movement is the explanation.
    """
    if sorted(order) != list(range(len(labels))):
        raise ValueError("order must be a permutation of the item positions")
    cells = []
    for position, source in enumerate(order):
        shift = source - position          # where it was, minus where it lands
        extra = item_classes[source] if item_classes else ""
        cells.append(
            f"<span class='{classes(SHIFT, extra)}' "
            f"style='--shift: {shift}; {_delay(position, step)}'>"
            f"{labels[source]}</span>"
        )
    columns = f"grid-template-columns: repeat({len(labels)}, minmax(0, 1fr));"
    return f"<div class='s101-row' style='{columns}'>{''.join(cells)}</div>"


def fit(characters: int, groups: int) -> tuple:
    """The type size and gap this row can afford, in that order of preference.

    Keep the type as large as possible, and spend whatever width is left on
    the gaps, because the gap is how far a digit travels. Returns strings
    ready for CSS.

    `groups` must be the *larger* of the two groupings being animated between.
    Going from pairs to threes, the row is at its widest at the very start -
    pairs make more blocks - and that is the moment that has to fit, or the
    end of the table is clipped exactly as it begins to move.

    One case cannot fit and is not made to: a long table read in single
    digits, where every character is its own block. There, legibility wins -
    the gap stops at FLOOR_GAP and the row scrolls - because squeezing the
    blocks together until they fit would defeat the point of separating them.
    """
    gaps = max(1, groups - 1)
    for size, cell in CELL_PX:
        spare = COLUMN_PX - characters * cell
        if spare <= 0:
            continue
        gap = min(IDEAL_GAP, spare / gaps / 16 * 0.92)   # 8% kept back
        if gap >= 0.5 or size == CELL_PX[-1][0]:
            return f"{size}rem", f"{max(FLOOR_GAP, gap):.2f}rem"
    return f"{CELL_PX[-1][0]}rem", f"{FLOOR_GAP}rem"


def cascade(groups: int) -> float:
    """Seconds between one group starting to move and the next.

    Spread over a fixed budget, so a long table does not take proportionally
    longer to regroup than a short one.
    """
    if groups < 2:
        return 0.0
    return min(STAGGER_MAX, STAGGER_BUDGET / (groups - 1))


def regroup(characters: str, was: int, now: int, *, step: Optional[float] = None) -> str:
    """One sequence of characters, re-gathered into blocks of a new width.

    Nothing moves position in the sequence - the characters are the same, in
    the same order. What changes is where the gaps fall, so each character
    slides by however many gaps now sit to its left. A digit table printed in
    pairs, read in threes, is the case this was written for: the student picks
    the width and watches the digits gather, instead of being told.

    `was` is the width the sequence is currently grouped in, `now` the width
    it should end up in. `was` is used only to size the row for the widest
    moment of the move; the movement itself needs no knowledge of it, because
    the browser interpolates from wherever each character already is. The
    blocks start moving left to right, which reads as regrouping rather than
    as everything twitching at once.
    """
    if now < 1 or was < 1:
        raise ValueError("a block is at least one character wide")
    if step is None:
        step = cascade(-(-len(characters) // now))
    span = len(characters)
    font, gap = fit(span, max(-(-span // was), -(-span // now)))
    cells = []
    for index, character in enumerate(characters):
        group = index // now
        delay = f"transition-delay: {group * step:.3f}s;" if step and group else ""
        cells.append(
            f"<span class='ch g{group % 2}' style='--block: {group}; {delay}'>"
            f"{character}</span>"
        )
    return (f"<div class='s101-seq' style='font-size: {font}; --gap: {gap};'>"
            f"{''.join(cells)}</div>")


def one(label: str, *, animation: str = POP, item_class: str = "") -> str:
    """A single thing, animated: the block that was just decided, say."""
    return f"<span class='{classes(animation, item_class)}'>{label}</span>"
