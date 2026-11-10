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
    if kind == "interval":
        return (f"The {q['noun']} are numbered 1 to {q['population']}. A systematic "
                f"sample was taken, and two of the {q['noun']} in it are numbered "
                f"{q['a']} and {q['b']}. Find the smallest possible size of that "
                "sample.")
    if kind == "representative":
        return (f"The table shows how the {q['noun']} are divided into groups, and how "
                f"many of each group were in a sample of {q['n']}. Decide whether the "
                f"sample is representative of all {q['population']} {q['noun']}.")
    return ""


def population_and_sample(q: Dict) -> str:
    """The group sizes beside the sample's make-up.

    The comparison is the question, so both columns have to be on the page -
    the expected numbers cannot be worked out from the sample alone.
    """
    rows = "".join(f"| {group} | {size} | {seen} |\n"
                   for group, size, seen in zip(q["groups"], q["sizes"], q["observed"]))
    return (f"| {q['noun'].title()} | In the population | In the sample |\n"
            "|---|---:|---:|\n" + rows
            + f"| **Total** | **{q['population']}** | **{q['n']}** |")


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

    if q["kind"] == "representative":
        st.markdown(population_and_sample(q))
    if q["kind"] in TABLE_KINDS:
        table.printed_row(q["row"])
        # The reader chooses the block width and sees the digits regroup. The
        # app does not say which width this question wants: working that out
        # is the skill, and the marking will show whether it was right.
        table.regrouper(q["row"], key=prefix,
                        labelled=f"The {q.get('noun', 'members')} are numbered "
                                 f"{label_range(q)}.")

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
                    " ".join(engine.pad_all(result.sample, result.width))))

        elif q["kind"] == "interval":
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
            st.write("**How many of each group would you expect in the sample?**")
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
                    "; ".join(f"{size}/{q['population']} \u00d7 {q['n']} = {want}"
                              for size, want in zip(q["sizes"], q["expected"]))))
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
                table.coloured_sample(result, q["strata"])

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


EXAMPLE_CODE = 1204   # the worked examples on "How it is done"


def page_learn() -> None:
    ui.inject()
    ui.page_header(TOPIC_LINE, "How it is done")
    tabs = st.tabs(["Reading the table", "Simple random", "Systematic", "Stratified",
                    "Representative?", "In the exam"])
    def example_for(kind):
        """A worked example, generated like any other question.

        A fixed code, so the example on this page is the same one every time
        and can be referred to in a lesson.
        """
        return generate.build(kind, EXAMPLE_CODE)

    with tabs[0]:
        ui.from_content(content.text, content.READING)
        example = example_for("simple")
        if example:
            st.markdown("**Try it on this table**")
            st.caption(example["setting"])
            table.printed_row(example["row"])
            table.regrouper(example["row"], key="learn-reading",
                            labelled=f"Here the students are numbered "
                                     f"{label_range(example)}.")
            st.divider()
            st.caption("Read in the width the labels need, this is what happens:")
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
                with st.expander(f"A worked example (code {EXAMPLE_CODE})"):
                    ui.scenario(example["setting"], task_text(example))
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


# The wording is the syllabus's and the mark schemes': a sampling frame, a
# sampling interval, a group that has been fully sampled. The options are
# stacked rather than placed side by side, because a row of four columns cuts
# the labels short and there is no shorter way to say "not in the sampling
# frame" that still says it.
DRILL_OPTIONS = {
    "simple": [("Select this number", R_IN_RANGE),
               ("Reject - not in the sampling frame", R_OUT_OF_RANGE),
               ("Reject - already selected", R_REPEAT)],
    "systematic": [("Use as the random start", R_IN_RANGE),
                   ("Reject - greater than the sampling interval", R_OVER_INTERVAL),
                   ("Reject - not in the sampling frame", R_OUT_OF_RANGE)],
    "stratified": [("Select this number", R_IN_RANGE),
                   ("Skip - that group is fully sampled", R_GROUP_FULL),
                   ("Reject - already selected", R_REPEAT),
                   ("Reject - not in the sampling frame", R_OUT_OF_RANGE)],
}



# What the table is being used to choose decides how wide the numbers are, and
# when to stop reading. This is the distinction the drill exists to teach: in a
# systematic sample the table picks one thing only, the random start.
# What each method has to settle before the table is any use.
FIRST_STAGE = {"systematic": "interval", "stratified": "split"}

WHAT_THE_TABLE_CHOOSES = {
    "simple": "You are choosing every member of the sample straight from the "
              "table, so the numbers have to reach the largest label in the "
              "population.",
    "stratified": "You are choosing every member of the sample straight from the "
                  "table, so the numbers have to reach the largest label in the "
                  "population.",
    "systematic": "You are choosing one thing only: the random start. Everything "
                  "after it is found by adding the sampling interval, so the "
                  "numbers only have to reach the end of the first interval.",
}

FIND_THE_INTERVAL = (
    "A systematic sample takes every kth member, counting on from a random "
    "start. Everything else here depends on k, so work it out before you read "
    "anything from the table."
)

FIND_THE_SPLIT = (
    "A stratified sample takes from each stratum in proportion to its size, so "
    "the sample has the same make-up as the population. Work out how many come "
    "from each one before you read anything from the table."
)

WHEN_TO_STOP = {
    "simple": "Read on until the sample is full.",
    "stratified": "Read on until every stratum is full.",
    "systematic": "Stop at the first number that can be the start. The table's "
                  "work is finished there.",
}


def needed_width(q: Dict, result) -> Tuple[int, int, int]:
    """The width the question needs, and the range of numbers it has to cover."""
    if q["kind"] == "systematic":
        lo = q["lo"]
        return read_width(q), lo, lo + result.interval - 1
    if q["kind"] == "stratified":
        hi = max(x.hi for x in q["strata"])
        return engine.label_width(hi), 1, hi
    return engine.label_width(q["hi"]), q["lo"], q["hi"]


def width_verdict(q: Dict, chosen: int, result) -> Tuple[bool, str]:
    """Why the chosen width is right or wrong, in terms of what is being chosen."""
    want, lo, top = needed_width(q, result)
    biggest = 10 ** chosen - 1
    span = f"{engine.pad(lo, want)} to {engine.pad(top, want)}"

    if chosen == want:
        if q["kind"] == "systematic":
            return True, (f"Yes. The start has to be one of the first "
                          f"{result.interval} members, so the numbers run {span}, "
                          f"and that needs {want} digits. The population is "
                          f"numbered up to {q['hi']}, but you are not choosing a "
                          "member of it here.")
        return True, (f"Yes. The numbers have to cover the whole population, "
                      f"{span}, and that needs {want} digits.")

    if q["kind"] == "systematic" and chosen == engine.label_width(q["hi"]):
        return False, (f"That is the width of the population's labels, which is "
                       f"what you would read to choose a member. Here the table "
                       f"is only choosing the random start, and a start cannot be "
                       f"past the sampling interval of {result.interval}. The "
                       f"numbers you need run {span}.")
    if chosen < want:
        return False, (f"Reading in {chosen}s gives numbers no larger than "
                       f"{biggest}, so most of {span} could never come up.")
    return False, (f"Reading in {chosen}s gives numbers as large as {biggest}, "
                   f"far beyond {span}. Almost every number would be rejected, "
                   "and some members could never be reached.")


def _explain(q: Dict, step, result) -> str:
    value = engine.pad(step.value, read_width(q))
    lo, hi = ((1, max(s.hi for s in q["strata"])) if q["kind"] == "stratified"
              else (q["lo"], q["hi"]))
    w = engine.label_width(hi)
    rng = f"{engine.pad(lo, w)} to {engine.pad(hi, w)}"
    if step.reason == R_OUT_OF_RANGE:
        return (f"`{value}` is outside {rng}, so it is not in the sampling frame: no "
                "member has that number. Read the next number.")
    if step.reason == R_REPEAT:
        return f"`{value}` has already been selected, and a member cannot be chosen twice."
    if step.reason == R_GROUP_FULL:
        return (f"`{value}` is in {step.stratum}, which has already been fully "
                "sampled. Skip it and carry on along the table.")
    if step.reason == R_OVER_INTERVAL:
        top = q["lo"] + result.interval - 1
        sw = engine.label_width(top)
        return (f"`{value}` is in the sampling frame, but the sampling interval is "
                f"{result.interval}, so the random start has to be between "
                f"{engine.pad(q['lo'], sw)} and {engine.pad(top, sw)}. Being a member "
                "of the population is not enough.")
    if q["kind"] == "systematic":
        return (f"`{value}` is within the first interval, so it is the random start. "
                f"Adding {result.interval} each time gives the rest of the sample.")
    if q["kind"] == "stratified":
        return f"`{value}` is in {step.stratum}, which still needs members, so it is selected."
    return f"`{value}` is inside {rng} and has not been selected before, so it is selected."


def page_drill() -> None:
    ui.inject()
    ui.page_header(TOPIC_LINE, "Selecting step by step",
                   "First decide how to read the table, then rule on each number.")

    state = st.session_state.setdefault("drill", {})
    c1, c2, c3 = st.columns([2, 1, 1])
    kind = c1.selectbox("Method", list(TABLE_KINDS),
                        format_func=lambda k: KIND_NAMES[k], key="drill_kind")
    if c2.button("New table", use_container_width=True) or state.get("kind") != kind:
        state.clear()
        state.update(kind=kind, seed=generate.new_seed(),
                     stage=FIRST_STAGE.get(kind, "width"),
                     i=0, right=0, wrong=0, last=None, width_choice=None,
                     interval_answer=None, split_answer=None)
    c3.caption(f"Code {state.get('seed', '')}")

    q = generate.build(kind, state["seed"])
    result = solve(q)
    width = read_width(q)
    ui.scenario(q["setting"], task_text(q))
    table.printed_row(q["row"])

    stage = state.get("stage") or FIRST_STAGE.get(kind, "width")
    if stage == "interval":
        _find_the_interval(q, result, state)
    elif stage == "split":
        _find_the_split(q, result, state)
    elif stage == "width":
        _choose_the_width(q, result, width, state)
    else:
        _rule_on_each_number(q, result, width, state)


def _find_the_interval(q: Dict, result, state: Dict) -> None:
    """Step one, systematic only: work out k.

    Printing the interval and asking the next question underneath it is the
    way a slide does it, and it is exactly what a student skims past. Here it
    has to be produced before anything else happens.
    """
    st.markdown("**Step 1 of 3 · What is the sampling interval?**")
    st.info(FIND_THE_INTERVAL)
    with st.form(f"interval:{state['seed']}"):
        given = st.number_input("The sampling interval", min_value=1, step=1, value=1,
                                key=f"interval:{state['seed']}:value")
        checked = st.form_submit_button("Check", type="primary")
    if checked:
        state["interval_answer"] = int(given)
        state["interval_tries"] = state.get("interval_tries", 0) + 1
        if int(given) != result.interval:
            state["interval_wrong"] = state.get("interval_wrong", 0) + 1
        st.rerun()

    answer = state.get("interval_answer")
    if answer is None:
        return
    if answer == result.interval:
        every = q["noun"][:-1] if q["noun"].endswith("s") else q["noun"]
        st.success(f"Yes. {q['population']} \u00f7 {q['n']} = {result.interval}, so "
                   f"once you have a start you take every {result.interval}th "
                   f"{every}.")
        if st.button("Next: how to read the table", type="primary"):
            state["stage"] = "width"
            st.rerun()
        return
    if state.get("interval_tries", 0) < 2:
        st.error(f"Not {answer}. The interval is how far apart the members of the "
                 "sample are: the size of the population divided by the size of "
                 "the sample. Try again.")
        return
    st.error(f"Not {answer}. There are {q['population']} {q['noun']} and the sample "
             f"is {q['n']}, so the interval is {q['population']} \u00f7 {q['n']} = "
             f"{result.interval}. Enter that to go on.")


def _find_the_split(q: Dict, result, state: Dict) -> None:
    """Step one, stratified only: how many come from each stratum.

    Shown as a banner above the table, this is read past. Produced first, it
    is the thing the rest of the question is built on.
    """
    st.markdown("**Step 1 of 3 · How many from each stratum?**")
    st.info(FIND_THE_SPLIT)
    population = sum(x.size for x in q["strata"])
    rows = "".join(f"| {x.name} | {x.size} |\n" for x in q["strata"])
    st.markdown(f"| Stratum | In the population |\n|---|---:|\n{rows}"
                f"| **Total** | **{population}** |")
    st.caption(f"A sample of {q['n']} is wanted.")

    want = [sh.count for sh in result.shares]
    with st.form(f"split:{state['seed']}"):
        cols = st.columns(len(q["strata"]))
        given = [c.number_input(x.name, min_value=0, step=1, value=0,
                                key=f"split:{state['seed']}:{x.name}")
                 for c, x in zip(cols, q["strata"])]
        checked = st.form_submit_button("Check", type="primary")
    if checked:
        state["split_answer"] = [int(g) for g in given]
        state["split_tries"] = state.get("split_tries", 0) + 1
        if [int(g) for g in given] != want:
            state["split_wrong"] = state.get("split_wrong", 0) + 1
        st.rerun()

    answer = state.get("split_answer")
    if answer is None:
        return
    working = ";  ".join(sh.working(population, q["n"]) for sh in result.shares)
    if answer == want:
        st.success(f"Yes. {working}. They add to {q['n']}, the size of the sample.")
        if st.button("Next: how to read the table", type="primary"):
            state["stage"] = "width"
            st.rerun()
        return
    if sum(answer) != q["n"]:
        st.error(f"Those add to {sum(answer)}, but the sample is {q['n']}. "
                 "Every member of the sample comes from one stratum, so the "
                 "numbers have to total the sample size.")
    elif state.get("split_tries", 0) < 2:
        st.error(f"They add to {q['n']}, but they are not in proportion. Each "
                 "stratum's share is its size divided by the size of the "
                 "population, times the size of the sample.")
    if state.get("split_tries", 0) >= 2:
        st.error(f"The proportions are {working}. Enter those to go on.")


def _choose_the_width(q: Dict, result, width: int, state: Dict) -> None:
    """Step two: what is the table being used to choose, and how wide is it?"""
    staged = q["kind"] in ("systematic", "stratified")
    st.markdown(f"**Step {'2 of 3' if staged else '1 of 2'} · How many "
                "digits do you read together?**")
    st.info(WHAT_THE_TABLE_CHOOSES[q["kind"]])
    if q["kind"] == "systematic":
        st.caption(f"You found the interval: **{result.interval}**.")
    if q["kind"] == "stratified":
        st.caption("You found the split: **"
                   + "**, **".join(f"{sh.count} {sh.name}" for sh in result.shares)
                   + "**.")

    cols = st.columns(4)
    for col, choice in zip(cols, (1, 2, 3, 4)):
        label = "1 digit" if choice == 1 else f"{choice} digits"
        if col.button(label, key=f"width:{state['seed']}:{choice}",
                      use_container_width=True):
            right, why = width_verdict(q, choice, result)
            state["width_choice"] = choice
            state["width_last"] = (right, why)
            state["width_tries"] = state.get("width_tries", 0) + 1
            if not right:
                state["width_wrong"] = state.get("width_wrong", 0) + 1
            st.rerun()

    chosen = state.get("width_choice")
    if not chosen:
        return
    st.caption(f"Read in blocks of {chosen}, the table gives:")
    table.blocks(q["row"], chosen, revealed=0)
    right, why = state["width_last"]
    (st.success if right else st.error)(why)
    if right and st.button("Now rule on each number", type="primary"):
        state["stage"] = "numbers"
        st.rerun()


def _rule_on_each_number(q: Dict, result, width: int, state: Dict) -> None:
    """Step two: the numbers themselves, one at a time."""
    last = "3 of 3" if q["kind"] in ("systematic", "stratified") else "2 of 2"
    st.markdown(f"**Step {last} · Reading in blocks of {width}**")
    st.caption(WHEN_TO_STOP[q["kind"]])
    i = state["i"]
    total = len(result.steps)
    table.blocks(q["row"], width, result.steps, revealed=i,
                 current=i if i < total else None, just=i - 1 if i else None)
    table.legend()

    if i < total:
        step = result.steps[i]
        st.markdown(f"Number {i + 1} of the table is")
        ui.big(step.block)
        st.write("")
        for text, reason in DRILL_OPTIONS[q["kind"]]:
            if st.button(text, key=f"drill:{state['seed']}:{i}:{reason}",
                         use_container_width=True):
                ok = reason == step.reason
                state["right" if ok else "wrong"] += 1
                state["last"] = (ok, _explain(q, step, result))
                state["i"] = i + 1
                st.rerun()
    else:
        if q["kind"] == "systematic":
            st.success("That is the random start, so the table's work is done. "
                       "The rest of the sample is arithmetic.")
        else:
            st.success("You have read as much of the table as the question needs.")
        st.markdown("**The sample**")
        if q["kind"] == "stratified":
            table.coloured_sample(result, q["strata"])
        else:
            table.sample_chips(result.sample, result.width)
        if q["kind"] == "systematic":
            st.markdown(f"Start `{engine.pad(result.start, result.width)}`, "
                        f"interval **{result.interval}**, so the sample is "
                        + " ".join(engine.pad_all(result.sample, result.width)))
        judged = state["right"] + state["wrong"]
        if judged:
            st.metric("Decisions you got right", f"{state['right']} / {judged}")
        if state.get("split_wrong"):
            st.caption(f"The split took {state['split_wrong'] + 1} attempts.")
        if state.get("interval_wrong"):
            st.caption(f"The sampling interval took "
                       f"{state['interval_wrong'] + 1} attempts.")
        if state.get("split_wrong"):
            st.caption(f"The split took {state['split_wrong'] + 1} attempts.")
        if state.get("interval_wrong"):
            st.caption(f"The sampling interval took {state['interval_wrong'] + 1} "
                       "attempts.")
        if state.get("width_wrong"):
            st.caption(f"You also tried {state['width_wrong']} other width"
                       f"{'s' if state['width_wrong'] > 1 else ''} before reading "
                       "the table.")
        if st.button("Another table", type="primary"):
            state.update(seed=generate.new_seed(),
                         stage=FIRST_STAGE.get(q["kind"], "width"),
                         i=0, right=0, wrong=0, last=None, width_choice=None,
                         width_tries=0, width_wrong=0, interval_answer=None,
                         interval_tries=0, interval_wrong=0, split_answer=None,
                         split_tries=0, split_wrong=0)
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
