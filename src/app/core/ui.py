"""The look of the app: stylesheet and the small pieces every topic reuses."""

from typing import Iterable, Optional, Sequence, Tuple

import streamlit as st

CSS = """
<style>
.block-container {padding-top: 2.1rem;}
.mono {font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
       font-size: 1.12rem; letter-spacing: .04em; line-height: 2.5; margin: .2rem 0 .4rem;}
.mono .blk {padding: .22rem .45rem; border-radius: .4rem; margin-right: .28rem;
            border: 1px solid transparent; white-space: nowrap;}
.mono .pend {color: #64748b; border-color: #e2e8f0;}
.mono .acc  {background: #dcfce7; color: #14532d; border-color: #86efac; font-weight: 700;}
.mono .rej  {background: #fee2e2; color: #991b1b; border-color: #fca5a5;
             text-decoration: line-through;}
.mono .skp  {background: #fef3c7; color: #78350f; border-color: #fcd34d;}
.mono .cur  {background: #1e293b; color: #f8fafc; border-color: #0f172a; font-weight: 700;}
.printed {font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
          font-size: 1.12rem; letter-spacing: .12em; color: #334155;
          background: #f8fafc; border: 1px solid #e2e8f0; border-radius: .5rem;
          padding: .7rem .9rem; margin: .2rem 0 .6rem;}
.legend {font-size: .82rem; color: #64748b; margin: -.2rem 0 .8rem;}
.legend span {margin-right: 1rem;}
.legend i {display: inline-block; width: .7rem; height: .7rem; border-radius: .2rem;
           margin-right: .3rem; vertical-align: middle;}
.chips span {display: inline-block; font-family: ui-monospace, Menlo, Consolas, monospace;
             background: #1e293b; color: #f8fafc; border-radius: .4rem;
             padding: .25rem .6rem; margin: 0 .35rem .35rem 0; font-size: 1.05rem;}
.scen {background: #f1f5f9; border-left: 4px solid #475569; border-radius: .35rem;
       padding: .8rem 1rem; margin-bottom: .8rem;}
.scen p {margin: 0;}
.scen .task {font-weight: 600; margin-top: .45rem;}
.srcnote {font-size: .85rem; color: #64748b; margin-top: -.4rem;}
.big {font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 2.6rem;
      font-weight: 700; letter-spacing: .06em; line-height: 1.2;}
.card {border: 1px solid #e2e8f0; border-radius: .6rem; padding: 1rem 1.1rem;
       margin-bottom: .9rem;}
.card h4 {margin: 0 0 .2rem;}
.card .meta {font-size: .85rem; color: #64748b; margin: 0 0 .5rem;}
@media (prefers-color-scheme: dark) {
  .printed {background: #1e293b; color: #e2e8f0; border-color: #334155;}
  .scen {background: #1e293b; border-left-color: #94a3b8;}
  .mono .pend {color: #94a3b8; border-color: #334155;}
  .card {border-color: #334155;}
}
</style>
"""


def inject() -> None:
    """Called once per page, since every rerun starts from the entry script."""
    st.markdown(CSS, unsafe_allow_html=True)


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

    Returns (chosen option or None, seed). The code is the seed, so a teacher can
    put one on the board and every student gets the same question.
    """
    state = st.session_state.setdefault(state_key, {})
    if options:
        cols = st.columns([3, 1, 1])
        chosen = cols[0].selectbox(label, list(options), format_func=format_func,
                                   key=f"{state_key}:choice")
    else:
        cols = st.columns([1, 1])
        chosen = None
    if cols[-2].button("New question", use_container_width=True,
                       key=f"{state_key}:new") or state.get("choice") != chosen:
        state.update(choice=chosen, seed=new_seed())
    state.setdefault("seed", new_seed())
    typed = cols[-1].text_input("Code", value=str(state["seed"]), key=f"{state_key}:code")
    if typed.strip().isdigit() and int(typed) != state["seed"]:
        state["seed"] = int(typed)
    return chosen, state["seed"]
