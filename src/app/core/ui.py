"""The look of the app: stylesheet and the small pieces every topic reuses."""

from typing import Iterable, Optional, Sequence, Tuple

import streamlit as st

from . import motion
from .library import ContentError

CSS = """
<style>
/* Theme-agnostic by necessity: Streamlit exposes no theme variables, and an
   OS-level prefers-color-scheme rule is wrong whenever the app's theme and the
   operating system disagree. So nothing here sets a background without
   letting the text keep the theme's own colour: fills are translucent greys
   and tints that sit correctly on a white or a near-black page. */
.block-container {padding-top: 2.1rem;}

.mono {font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
       font-size: 1.12rem; letter-spacing: .04em; line-height: 2.6; margin: .2rem 0 .4rem;}
.mono .blk {padding: .22rem .45rem; border-radius: .4rem; margin-right: .28rem;
            border: 1px solid transparent; white-space: nowrap; color: inherit;}
.mono .pend {opacity: .5; border-color: rgba(128,128,128,.3);}
.mono .acc  {background: rgba(34,197,94,.26);  border-color: rgba(34,197,94,.7);
             font-weight: 700;}
.mono .rej  {background: rgba(239,68,68,.22);  border-color: rgba(239,68,68,.65);
             text-decoration: line-through;}
.mono .skp  {background: rgba(245,158,11,.26); border-color: rgba(245,158,11,.7);}
.mono .cur  {background: rgba(128,128,128,.16); border: 2px solid currentColor;
             font-weight: 800; box-shadow: 0 0 0 3px rgba(128,128,128,.14);}

.printed {font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
          font-size: 1.12rem; letter-spacing: .12em; color: inherit;
          background: rgba(128,128,128,.12); border: 1px solid rgba(128,128,128,.32);
          border-radius: .5rem; padding: .7rem .9rem; margin: .2rem 0 .6rem;}

.legend {font-size: .82rem; opacity: .75; color: inherit; margin: -.2rem 0 .8rem;}
.legend span {margin-right: 1rem;}
.legend i {display: inline-block; width: .7rem; height: .7rem; border-radius: .2rem;
           margin-right: .3rem; vertical-align: middle;
           border: 1px solid rgba(128,128,128,.45);}

.chips span {display: inline-block; font-family: ui-monospace, Menlo, Consolas, monospace;
             background: rgba(128,128,128,.18); color: inherit; font-weight: 600;
             border: 1px solid rgba(128,128,128,.4); border-radius: .4rem;
             padding: .25rem .6rem; margin: 0 .35rem .35rem 0; font-size: 1.05rem;}

.scen {background: rgba(128,128,128,.12); color: inherit;
       border-left: 4px solid rgba(128,128,128,.6); border-radius: .35rem;
       padding: .8rem 1rem; margin-bottom: .8rem;}
.scen p {margin: 0;}
.scen .task {font-weight: 600; margin-top: .45rem;}

.srcnote {font-size: .85rem; opacity: .75; color: inherit; margin-top: -.4rem;}

.big {font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 2.6rem;
      font-weight: 700; letter-spacing: .06em; line-height: 1.2; color: inherit;}

.card {border: 1px solid rgba(128,128,128,.35); border-radius: .6rem;
       padding: 1rem 1.1rem; margin-bottom: .9rem; color: inherit;}
.card h4 {margin: 0 0 .2rem;}
.card .meta {font-size: .85rem; opacity: .75; margin: 0 0 .5rem;}
</style>
"""


def inject() -> None:
    """Called once per page, since every rerun starts from the entry script."""
    st.markdown(CSS + motion.CSS, unsafe_allow_html=True)


def from_content(fetch, *args) -> None:
    """Draw a content file. A missing file or heading becomes a note on the
    page naming the file, rather than a traceback."""
    try:
        st.markdown(fetch(*args))
    except ContentError as exc:
        st.warning(f"Content needs attention: {exc}")


def page_header(topic_line: str, title: str, caption: str = "") -> None:
    st.caption(topic_line)
    st.header(title)
    if caption:
        st.caption(caption)


def scenario(setting: str, task: str, source: str = "") -> None:
    st.markdown(f"<div class='scen'><p>{setting}</p><p class='task'>{task}</p></div>",
                unsafe_allow_html=True)
    if source:
        st.markdown(f"<p class='srcnote'>From: {source}</p>", unsafe_allow_html=True)


def mono_blocks(blocks: Sequence[Tuple[str, str]], caption: str = "") -> None:
    """A row of monospace blocks, each with a style class: the shared look for
    tables of digits, class intervals, data values - anything read left to right."""
    if caption:
        st.caption(caption)
    body = "".join(f"<span class='blk {cls}'>{text}</span>" for text, cls in blocks)
    st.markdown(f"<div class='mono'>{body}</div>", unsafe_allow_html=True)


def printed(text: str, caption: str = "") -> None:
    if caption:
        st.caption(caption)
    st.markdown(f"<div class='printed'>{text}</div>", unsafe_allow_html=True)


def legend(items: Sequence[Tuple[str, str]]) -> None:
    body = "".join(f"<span><i style='background:{colour}'></i>{label}</span>"
                   for label, colour in items)
    st.markdown(f"<div class='legend'>{body}</div>", unsafe_allow_html=True)


def chips(labels: Iterable[str]) -> None:
    body = "".join(f"<span>{label}</span>" for label in labels)
    st.markdown(f"<div class='chips'>{body}</div>", unsafe_allow_html=True)


def big(text: str) -> None:
    st.markdown(f"<div class='big'>{text}</div>", unsafe_allow_html=True)


def card(title: str, meta: str, body: str) -> None:
    st.markdown(f"<div class='card'><h4>{title}</h4><p class='meta'>{meta}</p>{body}</div>",
                unsafe_allow_html=True)


def code_controls(state_key: str, new_seed, label: str = "Question type",
                  options: Optional[Sequence[str]] = None, format_func=str):
    """The row every practice page needs: what to practise, a new question, the code.

    Returns (chosen option or None, seed). The code *is* the seed, so the same
    code gives the same question on any machine.

    The code box carries a widget key, which means its stored value wins over
    anything passed as `value=`. So when a new seed is drawn, the box's own
    session state has to be written before the widget is created on this run -
    otherwise the box hands back the previous code and the question never
    changes.
    """
    state = st.session_state.setdefault(state_key, {})
    code_key = f"{state_key}:code"

    if options:
        columns = st.columns([3, 1, 1])
        chosen = columns[0].selectbox(label, list(options), format_func=format_func,
                                      key=f"{state_key}:choice")
    else:
        columns = st.columns([1, 1])
        chosen = None

    asked_for_another = columns[-2].button("New question", use_container_width=True,
                                           key=f"{state_key}:new")
    if asked_for_another or "seed" not in state or state.get("choice") != chosen:
        state["choice"] = chosen
        state["seed"] = new_seed()
        st.session_state[code_key] = str(state["seed"])

    st.session_state.setdefault(code_key, str(state["seed"]))
    typed = columns[-1].text_input("Code", key=code_key)
    if typed.strip().isdigit() and int(typed) != state["seed"]:
        state["seed"] = int(typed)
    return chosen, state["seed"]
