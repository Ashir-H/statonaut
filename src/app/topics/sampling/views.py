"""The pages of the random number tables topic."""

from typing import Dict, List, Optional, Sequence, Tuple

import streamlit as st

from app.core import scoring, ui
from app.core.library import ContentError

from . import content, engine, generate, table
from .engine import (ACCEPT, R_GROUP_FULL, R_IN_RANGE, R_OUT_OF_RANGE,
                     R_OVER_INTERVAL, R_REPEAT, Stratum)

TOPIC_LINE = "Unit 1 · Data and its collection · syllabus 1.2 and 1.4"

KIND_NAMES = {
    "simple": "Simple random sample",
    "systematic": "Systematic sample",
    "stratified": "Stratified sample",
    "interval": "Sample size from two members",
    "representative": "Is the sample representative?",
}

TABLE_KINDS = ("simple", "systematic", "stratified")


# ------------------------------------------------------------- shared bits


def solve(q: Dict):
    kind = q["kind"]
    if kind == "simple":
        return engine.simple_random(q["row"], q["lo"], q["hi"], q["n"])
    if kind == "systematic":
        return engine.systematic(q["row"], q["lo"], q["hi"], q["n"])
    if kind == "stratified":
        return engine.stratified(q["row"], q["strata"], q["n"])
    return None


def read_width(q: Dict) -> int:
    """How wide the blocks are when this question's table is read."""
    if q["kind"] == "systematic":
        return engine.start_read_width(q["lo"], q["hi"], q["n"])
    if q["kind"] == "stratified":
        return engine.label_width(max(s.hi for s in q["strata"]))
    if "hi" in q:
        return engine.label_width(q["hi"])
    return 2   # the question has no table of its own


def label_range(q: Dict) -> str:
    if q["kind"] == "stratified":
        lo, hi = 1, max(s.hi for s in q["strata"])
    else:
        lo, hi = q["lo"], q["hi"]
    w = engine.label_width(hi)
    return f"{engine.pad(lo, w)} to {engine.pad(hi, w)}"


def task_text(q: Dict) -> str:
    if "task" in q:
        return q["task"]
    kind = q["kind"]
    if kind == "simple":
        return (f"The {q['noun']} are numbered {label_range(q)}. Use the table below to "
                f"select a simple random sample of {q['n']} {q['noun']}.")
    if kind == "systematic":
        return (f"The {q['noun']} are numbered {label_range(q)}. Use the table below to "
                f"select a systematic sample of {q['n']} {q['noun']}.")
    if kind == "stratified":
        width = engine.label_width(max(s.hi for s in q["strata"]))
        groups = ", ".join(f"{s.name} numbered {s.label_range(width)}" for s in q["strata"])
        return (f"The {q['noun']} are numbered {label_range(q)}: {groups}. Select a "
                f"stratified sample of {q['n']} {q['noun']}.")
    return ""


def signature(q: Dict) -> str:
    return f"{q['kind']}|{q.get('id') or q.get('seed')}|{q.get('row', '')}"


def _sizes_part(q: Dict, given: Sequence[Optional[int]]) -> Dict:
    shares = engine.strata_shares(q["strata"], q["n"])
    population = sum(s.size for s in q["strata"])
    award = scoring.mark_count([sh.count for sh in shares],
                               [int(g) if g is not None else -1 for g in given], 2)
    return scoring.part("The group sizes", award,
                        "; ".join(sh.working(population, q["n"]) for sh in shares))


def _pairs(picks: Dict[str, List[int]]) -> List[Tuple[str, int]]:
    return sorted((name, v) for name, vs in picks.items() for v in vs)


# ------------------------------------------------------------ asking a question


def attempt(q: Dict, prefix: str, source: str = "", note: str = "") -> None:
    """Show a question, take an answer, mark it the way Cambridge would."""
    result = solve(q)
    width = read_width(q)
    ui.scenario(q["setting"], task_text(q), source)

    if q["kind"] in TABLE_KINDS:
        table.printed_row(q["row"])
        with st.expander("Show me the digits regrouped for reading"):
            table.blocks(q["row"], width, revealed=0)
            st.caption(
                f"Reading in blocks of {width}. "
                + ("The interval decides this width, not the labels."
                   if q["kind"] == "systematic" and width != engine.label_width(q["hi"])
                   else "This matches the width of the labels.")
            )

    with st.form(f"{prefix}:form"):
        parts: List[Dict] = []

        if q["kind"] == "simple":
            answer = st.text_input("Your sample, in the order you selected it",
                                   placeholder="e.g. 05 41 23", key=f"{prefix}:srs")
            submitted = st.form_submit_button("Mark my answer", type="primary")
            if submitted:
                parts.append(scoring.part(
                    "The sample",
                    scoring.mark_sample(result.sample, scoring.parse_numbers(answer),
                                        q["marks"]),
                    " ".join(engine.pad_all(result.sample, result.width))))

        elif q["kind"] == "systematic":
            c1, c2 = st.columns([1, 2])
            k_given = c1.number_input("The interval", min_value=1, step=1, value=1,
                                      key=f"{prefix}:k")
            answer = c2.text_input("Your sample", placeholder="e.g. 09 19 29",
                                   key=f"{prefix}:sys")
            submitted = st.form_submit_button("Mark my answer", type="primary")
            if submitted:
                parts.append(scoring.part("The interval",
                                          scoring.mark_value(result.interval, int(k_given)),
                                          str(result.interval)))
                parts.append(scoring.part(
                    "The sample",
                    scoring.mark_sample(result.sample, scoring.parse_numbers(answer), 2),
                    " ".join(engine.pad_all(result.sample, result.width))))

        elif q["kind"] == "stratified":
            st.write("**How many from each group?**")
            cols = st.columns(len(q["strata"]))
            sizes = [c.number_input(s.name, min_value=0, step=1, value=0,
                                    key=f"{prefix}:size:{s.name}")
                     for c, s in zip(cols, q["strata"])]
            st.write("**Which members did you select?**")
            cols = st.columns(len(q["strata"]))
            picked = [c.text_input(s.name, key=f"{prefix}:pick:{s.name}",
                                   placeholder="numbers")
                      for c, s in zip(cols, q["strata"])]
            submitted = st.form_submit_button("Mark my answer", type="primary")
            if submitted:
                parts.append(_sizes_part(q, sizes))
                want = _pairs(result.picks)
                got = sorted((s.name, v) for s, text in zip(q["strata"], picked)
                             for v in scoring.parse_numbers(text))
                errors = max(len([p for p in want if p not in got]),
                             len([p for p in got if p not in want]))
                parts.append(scoring.part(
                    "The selection",
                    scoring.Award(marks=max(0, q["marks"] - errors),
                                  available=q["marks"], errors=errors),
                    "; ".join(f"{name}: " + " ".join(engine.pad_all(vs, result.width))
                              for name, vs in result.picks.items())))

        elif q["kind"] == "interval":
            st.write(f"Two members of a systematic sample are **{q['a']}** and **{q['b']}**.")
            c1, c2 = st.columns(2)
            diff = c1.number_input("The difference between them", min_value=1, step=1,
                                   value=1, key=f"{prefix}:diff")
            size = c2.number_input("The smallest possible sample size", min_value=1,
                                   step=1, value=1, key=f"{prefix}:size")
            submitted = st.form_submit_button("Mark my answer", type="primary")
            if submitted:
                parts.append(scoring.part("The difference",
                                          scoring.mark_value(q["difference"], int(diff)),
                                          str(q["difference"])))
                parts.append(scoring.part(
                    "The sample size", scoring.mark_value(q["answer"], int(size)),
                    f"{q['population']} / {q['difference']} = {q['answer']}"))

        else:   # representative
            st.write("**The sample that was taken**")
            st.markdown(" | ".join(f"{g}: **{o}**"
                                   for g, o in zip(q["groups"], q["observed"])))
            st.write("**How many would you expect from each group?**")
            cols = st.columns(len(q["groups"]))
            expected = [c.number_input(g, min_value=0, step=1, value=0,
                                       key=f"{prefix}:exp:{g}")
                        for c, g in zip(cols, q["groups"])]
            verdict = st.radio("Is the sample representative?",
                               ["Yes, it is representative", "No, it is not representative"],
                               key=f"{prefix}:verdict", horizontal=True)
            st.text_area("Write your conclusion as you would in the exam",
                         key=f"{prefix}:words", height=80,
                         placeholder="Compare the numbers you found with the numbers "
                                     "you expected.")
            submitted = st.form_submit_button("Mark my answer", type="primary")
            if submitted:
                parts.append(scoring.part(
                    "The expected numbers",
                    scoring.mark_count(q["expected"], [int(e) for e in expected], 1),
                    " ".join(f"{g}: {e}" for g, e in zip(q["groups"], q["expected"]))))
                parts.append(scoring.part(
                    "The conclusion",
                    scoring.mark_value(q["fair"], verdict.startswith("Yes")),
                    "representative" if q["fair"] else "not representative"))

        if submitted:
            scoring.remember(prefix, signature(q), parts)
            st.rerun()

    outcome = scoring.recall(prefix, signature(q))
    if not outcome:
        return
    got = scoring.show_outcome(outcome["parts"])
    total = sum(p["available"] for p in outcome["parts"])

    if q["kind"] == "representative":
        st.markdown("**A conclusion that would earn the third mark**")
        pairs = ", ".join(f"{g}: {o} where {e} was expected"
                          for g, o, e in zip(q["groups"], q["observed"], q["expected"]))
        st.info(f"The sample contains {pairs}. "
                + ("The two sets of numbers agree, so the sample is representative."
                   if q["fair"] else
                   "The numbers do not agree, so the sample is not representative."))
        st.caption("Check your own sentence against that one: it has to quote both the "
                   "numbers you found and the numbers you expected, then conclude.")

    if q["kind"] in TABLE_KINDS:
        with st.expander("How the table was read, number by number", expanded=(got < total)):
            table.walkthrough(result, q["row"], width)
            if q["kind"] == "systematic":
                st.markdown(
                    f"The start is `{engine.pad(result.start, result.width)}` and the "
                    f"interval is **{result.interval}**, so the sample is "
                    + " ".join(engine.pad_all(result.sample, result.width)))
            if q["kind"] == "stratified":
                population = sum(s.size for s in q["strata"])
                st.markdown("**The group sizes**  \n" + "  \n".join(
                    sh.working(population, q["n"]) for sh in result.shares))

    with st.expander("What the mark scheme rewards"):
        if q["kind"] in content.METHOD_KINDS:
            ui.from_content(content.method_section, q["kind"], content.MARKS)
        elif q["kind"] == "interval":
            ui.from_content(content.text, content.INTERVAL_MARKS)
        else:
            ui.from_content(content.text, content.REPRESENTATIVE)
        if note:
            st.markdown(f"**About this question.** {note}")


# ------------------------------------------------------------------- pages


def page_learn() -> None:
    ui.inject()
    ui.page_header(TOPIC_LINE, "How it is done")
    tabs = st.tabs(["Reading the table", "Simple random", "Systematic", "Stratified",
                    "Representative?", "In the exam"])
    try:
        bank = content.questions()
    except ContentError as exc:
        bank = []
        st.warning(f"Content needs attention: {exc}")

    def example_for(kind):
        return next((q for q in bank if q["kind"] == kind), None)

    with tabs[0]:
        ui.from_content(content.text, content.READING)
        example = example_for("simple")
        if example:
            st.caption(f"Worked through: {example['setting']}")
            table.printed_row(example["row"])
            result = solve(example)
            table.walkthrough(result, example["row"], read_width(example))
            st.markdown("**The sample**")
            table.sample_chips(result.sample, result.width)

    for i, kind in enumerate(content.METHOD_KINDS, start=1):
        with tabs[i]:
            try:
                doc = content.method(kind)
            except ContentError as exc:
                st.warning(f"Content needs attention: {exc}")
                continue
            st.subheader(doc.title or KIND_NAMES[kind])
            ui.from_content(doc.section, content.IDEA)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**{doc.headings.get(content.METHOD, 'The method')}**")
                ui.from_content(doc.section, content.METHOD)
            with c2:
                st.markdown(f"**{doc.headings.get(content.WATCH, 'Where marks are lost')}**")
                ui.from_content(doc.section, content.WATCH)
            st.markdown(f"**{doc.headings.get(content.MARKS, 'How it is marked')}**")
            ui.from_content(doc.section, content.MARKS)
            example = example_for(kind)
            if example:
                with st.expander(f"A worked example - {example['source']}"):
                    ui.scenario(example["setting"], example["task"])
                    table.printed_row(example["row"])
                    res = solve(example)
                    table.walkthrough(res, example["row"], read_width(example))
                    if kind == "stratified":
                        population = sum(s.size for s in example["strata"])
                        st.markdown("**The group sizes**  \n" + "  \n".join(
                            sh.working(population, example["n"]) for sh in res.shares))
                    st.markdown("**The sample**")
                    table.sample_chips(res.sample, res.width)

    with tabs[4]:
        ui.from_content(content.text, content.REPRESENTATIVE)
    with tabs[5]:
        ui.from_content(content.text, content.EXAM_NOTES)
        ui.from_content(content.text, content.MISTAKES)


DRILL_OPTIONS = {
    "simple": [("Select it", R_IN_RANGE),
               ("Reject - outside the numbered range", R_OUT_OF_RANGE),
               ("Reject - already selected", R_REPEAT)],
    "systematic": [("Use it as the random start", R_IN_RANGE),
                   ("Reject - larger than the interval", R_OVER_INTERVAL),
                   ("Reject - outside the numbered range", R_OUT_OF_RANGE)],
    "stratified": [("Select it", R_IN_RANGE),
                   ("Skip - that group is already full", R_GROUP_FULL),
                   ("Reject - already selected", R_REPEAT),
                   ("Reject - outside the numbered range", R_OUT_OF_RANGE)],
}


def _explain(q: Dict, step, result) -> str:
    value = engine.pad(step.value, read_width(q))
    lo, hi = ((1, max(s.hi for s in q["strata"])) if q["kind"] == "stratified"
              else (q["lo"], q["hi"]))
    w = engine.label_width(hi)
    rng = f"{engine.pad(lo, w)} to {engine.pad(hi, w)}"
    if step.reason == R_OUT_OF_RANGE:
        return f"`{value}` is outside {rng}, so there is no such member. Read the next number."
    if step.reason == R_REPEAT:
        return f"`{value}` has already been selected, and a member cannot be chosen twice."
    if step.reason == R_GROUP_FULL:
        return (f"`{value}` is in {step.stratum}, and that group already has all the "
                "members it needs. Skip it and carry on along the table.")
    if step.reason == R_OVER_INTERVAL:
        top = q["lo"] + result.interval - 1
        sw = engine.label_width(top)
        return (f"`{value}` is a real member, but the interval is {result.interval}, so "
                f"the start has to be {engine.pad(q['lo'], sw)} to {engine.pad(top, sw)}. "
                "Being a member is not enough.")
    if q["kind"] == "systematic":
        return (f"`{value}` is within the first interval, so it is the random start. "
                f"Adding {result.interval} each time gives the rest of the sample.")
    if q["kind"] == "stratified":
        return f"`{value}` is in {step.stratum}, which still needs members, so it is selected."
    return f"`{value}` is inside {rng} and has not been selected before, so it is selected."


def page_drill() -> None:
    ui.inject()
    ui.page_header(TOPIC_LINE, "Walk the table",
                   "One number at a time. Decide what happens to it before you move on.")

    state = st.session_state.setdefault("drill", {})
    c1, c2, c3 = st.columns([2, 1, 1])
    kind = c1.selectbox("Method", list(TABLE_KINDS),
                        format_func=lambda k: KIND_NAMES[k], key="drill_kind")
    if c2.button("New table", use_container_width=True) or state.get("kind") != kind:
        state.clear()
        state.update(kind=kind, seed=generate.new_seed(), i=0, right=0, wrong=0, last=None)
    c3.caption(f"Code {state.get('seed', '')}")

    q = generate.build(kind, state["seed"])
    result = solve(q)
    width = read_width(q)
    ui.scenario(q["setting"], task_text(q))
    if kind == "systematic":
        st.info(f"The interval is {q['population']} / {q['n']} = **{result.interval}**, so "
                f"the random start must be one of the first {result.interval} members.")
    if kind == "stratified":
        population = sum(s.size for s in q["strata"])
        st.info("The sample splits as  " + " &nbsp;·&nbsp; ".join(
            sh.working(population, q["n"]) for sh in result.shares))

    table.printed_row(q["row"])
    i = state["i"]
    total = len(result.steps)
    table.blocks(q["row"], width, result.steps, revealed=i,
                 current=i if i < total else None)
    table.legend()

    if i < total:
        step = result.steps[i]
        st.markdown(f"Number {i + 1} of the table is")
        ui.big(step.block)
        st.write("")
        options = DRILL_OPTIONS[kind]
        cols = st.columns(len(options))
        for col, (text, reason) in zip(cols, options):
            if col.button(text, key=f"drill:{state['seed']}:{i}:{reason}",
                          use_container_width=True):
                ok = reason == step.reason
                state["right" if ok else "wrong"] += 1
                state["last"] = (ok, _explain(q, step, result))
                state["i"] = i + 1
                st.rerun()
    else:
        st.success("You have read as much of the table as the question needs.")
        st.markdown("**The sample**")
        table.sample_chips(result.sample, result.width)
        if kind == "stratified":
            st.markdown("  \n".join(
                f"**{name}**: " + " ".join(engine.pad_all(vs, result.width))
                for name, vs in result.picks.items()))
        if kind == "systematic":
            st.markdown(f"Start `{engine.pad(result.start, result.width)}`, "
                        f"interval **{result.interval}**.")
        judged = state["right"] + state["wrong"]
        if judged:
            st.metric("Decisions you got right", f"{state['right']} / {judged}")
        if st.button("Another table", type="primary"):
            state.update(seed=generate.new_seed(), i=0, right=0, wrong=0, last=None)
            st.rerun()

    if state.get("last"):
        ok, message = state["last"]
        (st.success if ok else st.error)(("Correct. " if ok else "Not that. ") + message)


def page_practice() -> None:
    ui.inject()
    ui.page_header(TOPIC_LINE, "Practice a whole question",
                   "Written and marked the way the papers do it.")
    kind, seed = ui.code_controls("practice", generate.new_seed,
                                 options=list(KIND_NAMES),
                                 format_func=lambda k: KIND_NAMES[k])
    attempt(generate.build(kind, seed), prefix=f"practice:{kind}:{seed}")
    st.caption("Share the code to give someone the same question.")


def page_bank() -> None:
    ui.inject()
    ui.page_header(TOPIC_LINE, "Questions from our own papers",
                   "Every one of these has been set in class, with its answer "
                   "already checked.")
    try:
        bank = content.questions()
    except ContentError as exc:
        st.error(f"Content needs attention: {exc}")
        return
    labels = {q["id"]: f"{q['source']} - {KIND_NAMES[q['kind']]}" for q in bank}
    chosen = st.selectbox("Question", [q["id"] for q in bank],
                          format_func=lambda i: labels[i], key="bank_choice")
    q = next(x for x in bank if x["id"] == chosen)
    attempt(q, prefix=f"bank:{chosen}", source=q["source"], note=q.get("note", ""))
