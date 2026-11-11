"""Putting values in ascending order by dragging them, the mark students lose.

Streamlit has no drag-to-reorder widget, so this is a self-contained page of
HTML in an iframe: the dragging, the check and the feedback all happen in the
browser, with no rerun and nothing sent back to Python. The cost is that Python
never learns the order, so this page teaches rather than marks. A markable
version would need a third-party component.

Two details are deliberate. Dragging is built on pointer events rather than the
HTML drag-and-drop API, because the latter does nothing on a touch screen and
half this app is read on a phone. And the colours are read off the parent page
at run time - st.iframe gives the frame same-origin access to the app - rather
than guessed from the operating system, which is the mistake that made the
first version of this app unreadable in dark mode.
"""

import json
from typing import Optional, Sequence

import streamlit as st

# Two modes, because the same dragging serves two different purposes.
#
# "learn" is an exercise: it checks the order and names the median, which is
# what the notes page wants.
#
# "working" is rough work beside a question that is about to be marked. It must
# not check anything and must not name the median, or the page would answer
# itself. The controls and the message are therefore built here rather than
# hidden by script, so that a page carrying no "Check the order" button
# genuinely has no way to reveal an answer.
LEARN, WORKING = "learn", "working"

HEIGHTS = {LEARN: 210, WORKING: 150}

_CONTROLS = {
    LEARN: ('<button id="check" type="button">Check the order</button>'
            '<button id="shuffle" type="button">Shuffle again</button>'),
    WORKING: '<button id="reset" type="button">Back to the given order</button>',
}

_MESSAGE = {LEARN: '<p id="say"></p>', WORKING: ""}

# The whole checker, lifted out of the page. Hiding the button would not be
# enough: the text that names the median would still sit in the page's source,
# where a student can read it, so a rough-work row is built without this code
# at all rather than with it switched off.
_CHECKERS = {LEARN: """var checkButton = document.getElementById("check");
if (checkButton) checkButton.addEventListener("click", function () {
  var now = current(), want = wanted(), right = true;
  clear();
  Array.prototype.forEach.call(row.children, function (chip, i) {
    var ok = now[i] === want[i];
    chip.classList.add(ok ? "good" : "bad");
    if (!ok) right = false;
  });
  if (!right) {
    if (say) say.textContent = "Not in ascending order yet. The values outlined in orange "
                    + "are not where they belong.";
    return;
  }
  var n = now.length, low = Math.ceil(n / 2) - 1, high = Math.floor(n / 2 + 0.5);
  if (n % 2) {
    row.children[(n - 1) / 2].classList.add("median");
    if (say) say.textContent = "In ascending order. There are " + n + " values, so the median is the "
                    + ((n + 1) / 2) + "th of them: " + now[(n - 1) / 2] + ".";
  } else {
    row.children[n / 2 - 1].classList.add("median");
    row.children[n / 2].classList.add("median");
    if (say) say.textContent = "In ascending order. There are " + n + " values, so the median sits "
                    + "halfway between the " + (n / 2) + "th and the "
                    + (n / 2 + 1) + "th: " + ((now[n / 2 - 1] + now[n / 2]) / 2)
                    + ".";
  }
});
""", WORKING: ""}

_HINTS = {
    LEARN: ("Smallest first. Drag a value, or focus one and use the left and "
            "right arrow keys."),
    WORKING: ("Smallest first. Drag a value, or focus one and use the arrow keys. "
              "Nothing here is marked - type your answers below."),
}


def ordering_html(values: Sequence[int], theme: Optional[str] = None,
                  mode: str = LEARN) -> str:
    """The whole exercise as one page. No Streamlit here, so it can be tested."""
    return (_TEMPLATE
            .replace("__CHECKER__", _CHECKERS[mode])
            .replace("__CONTROLS__", _CONTROLS[mode])
            .replace("__MESSAGE__", _MESSAGE[mode])
            .replace("__HINT__", _HINTS[mode])
            .replace("__VALUES__", json.dumps([int(v) for v in values]))
            .replace("__THEME__", json.dumps(theme)))


def ordering_exercise(values: Sequence[int], mode: str = LEARN) -> None:
    """Draw the exercise, matched to whichever theme the reader is using."""
    theme = None
    try:                                     # None under the test harness
        theme = st.context.theme.type
    except Exception:                        # noqa: BLE001 - older Streamlit
        theme = None
    alt = ("Drag the values into ascending order, then check the order."
           if mode == LEARN else
           "Drag the values into ascending order as rough work.")
    st.iframe(ordering_html(values, theme, mode), height=HEIGHTS[mode], alt=alt)


_TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8"><style>
:root {--ink:#2f2d2b; --soft:rgba(128,128,128,.18); --line:rgba(128,128,128,.45);
       --accent:#7F77DD; --good:#1D9E75; --bad:#D85A30;}
*{box-sizing:border-box}
body{margin:0; color:var(--ink); background:transparent;
     font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
#row{display:flex; gap:.4rem; flex-wrap:wrap; padding:.1rem 0 .7rem; min-height:2.6rem}
.chip{font-family:ui-monospace,Menlo,Consolas,monospace; font-size:1.15rem;
      font-weight:600; padding:.35rem .75rem; border-radius:.45rem;
      background:var(--soft); border:1px solid var(--line); cursor:grab;
      user-select:none; touch-action:none; color:inherit;
      transition:transform .16s ease, background .16s ease, border-color .16s ease}
.chip:focus-visible{outline:2px solid var(--accent); outline-offset:2px}
.chip.dragging{cursor:grabbing; opacity:.9; transition:none}
.chip.good{background:rgba(29,158,117,.22); border-color:var(--good)}
.chip.bad{background:rgba(216,90,48,.2); border-color:var(--bad)}
.chip.median{box-shadow:0 0 0 2px var(--accent)}
.controls{display:flex; gap:.4rem; align-items:center; flex-wrap:wrap}
button{font:inherit; padding:.35rem .8rem; border-radius:.45rem; cursor:pointer;
       border:1px solid var(--line); background:var(--soft); color:inherit}
#say{min-height:2.6em; font-size:.9rem; opacity:.9; margin:.6rem 0 0}
.hint{font-size:.8rem; opacity:.7; margin:.1rem 0 0}
@media (prefers-reduced-motion: reduce){.chip{transition:none}}
</style></head>
<body>
<div id="row"></div>
<div class="controls">__CONTROLS__</div>
__MESSAGE__
<p class="hint">__HINT__</p>
<script>
var VALUES = __VALUES__;
var THEME = __THEME__;
var row = document.getElementById("row");
var say = document.getElementById("say");

(function paint() {
  var colour = null;
  try {
    colour = window.parent.getComputedStyle(window.parent.document.body).color;
  } catch (e) { colour = null; }
  if (!colour || colour === "rgba(0, 0, 0, 0)") {
    colour = THEME === "dark" ? "#edebe8" : "#2f2d2b";
  }
  document.documentElement.style.setProperty("--ink", colour);
})();

function build(order) {
  row.innerHTML = "";
  order.forEach(function (v) {
    var chip = document.createElement("div");
    chip.className = "chip";
    chip.textContent = v;
    chip.tabIndex = 0;
    row.appendChild(chip);
  });
  if (say) say.textContent = "";
}

function current() {
  return Array.prototype.map.call(row.children, function (c) {
    return Number(c.textContent);
  });
}

function wanted() {
  return VALUES.slice().sort(function (a, b) { return a - b; });
}

function clear() {
  Array.prototype.forEach.call(row.children, function (c) {
    c.classList.remove("good", "bad", "median");
  });
}

/* Dragging. The dragged chip follows the pointer, and whenever it passes the
   middle of a neighbour the two swap places in the document, so the row
   reorders under the finger rather than after it is let go. */
var held = null, startX = 0;

row.addEventListener("pointerdown", function (event) {
  var chip = event.target.closest(".chip");
  if (!chip) return;
  held = chip;
  startX = event.clientX;
  chip.classList.add("dragging");
  chip.setPointerCapture(event.pointerId);
  clear();
});

row.addEventListener("pointermove", function (event) {
  if (!held) return;
  held.style.transform = "translateX(" + (event.clientX - startX) + "px)";
  var others = Array.prototype.filter.call(row.children, function (c) {
    return c !== held;
  });
  for (var i = 0; i < others.length; i++) {
    var box = others[i].getBoundingClientRect();
    var middle = box.left + box.width / 2;
    var before = others[i].compareDocumentPosition(held)
                 & Node.DOCUMENT_POSITION_FOLLOWING;
    if (before && event.clientX < middle) {
      row.insertBefore(held, others[i]);
      held.style.transform = "";
      startX = event.clientX;
      return;
    }
    if (!before && event.clientX > middle) {
      row.insertBefore(held, others[i].nextSibling);
      held.style.transform = "";
      startX = event.clientX;
      return;
    }
  }
});

function drop() {
  if (!held) return;
  held.classList.remove("dragging");
  held.style.transform = "";
  held = null;
}
row.addEventListener("pointerup", drop);
row.addEventListener("pointercancel", drop);

row.addEventListener("keydown", function (event) {
  var chip = event.target.closest(".chip");
  if (!chip) return;
  if (event.key === "ArrowLeft" && chip.previousElementSibling) {
    row.insertBefore(chip, chip.previousElementSibling);
  } else if (event.key === "ArrowRight" && chip.nextElementSibling) {
    row.insertBefore(chip, chip.nextElementSibling.nextSibling);
  } else {
    return;
  }
  event.preventDefault();
  chip.focus();
  clear();
});

__CHECKER__

var shuffleButton = document.getElementById("shuffle");
if (shuffleButton) shuffleButton.addEventListener("click", function () {
  var order = VALUES.slice(), want = wanted(), tries = 0;
  do {
    for (var i = order.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var swap = order[i]; order[i] = order[j]; order[j] = swap;
    }
    tries++;
  } while (tries < 20 && order.every(function (v, i) { return v === want[i]; }));
  build(order);
});

var reset = document.getElementById("reset");
if (reset) {
  reset.addEventListener("click", function () { build(VALUES.slice()); });
}

build(VALUES);
</script>
</body></html>
"""
