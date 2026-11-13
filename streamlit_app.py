"""Statonaut - practice for Cambridge IGCSE Statistics 0479.

Run it with:  uv run streamlit run streamlit_app.py

Use uv (or the project's own .venv). A bare `streamlit run` uses whichever
Streamlit is first on PATH, which may be an older one installed system-wide.

This file is the router. Every page lives in a topic package under
`src/app/topics/`, and the sidebar is built from `app.registry`, so adding a
topic does not mean editing this file.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))

import streamlit as st  # noqa: E402

from app import home, registry  # noqa: E402
from app.core import scoring  # noqa: E402

st.set_page_config(
    page_title="Statonaut",
    page_icon=":material/bar_chart:",
    layout="centered",
    # "auto" rather than "expanded": on a phone an expanded sidebar covers the
    # page and swallows the first tap. It still opens on a wide screen.
    initial_sidebar_state="auto",
)

# One section per topic, each holding that topic's pages. Section headings are
# what gives the sidebar its two levels: topic, then page.
sections = {
    "Statonaut": [
        st.Page(home.render, title="Home", icon=":material/home:",
                url_path="home", default=True),
    ],
}
for topic in registry.topics():
    sections[topic.section] = [
        st.Page(page.render, title=page.title, icon=page.icon,
                url_path=registry.url_path(topic, page), help=page.blurb)
        for page in topic.pages
    ]

for extra in registry.standalone():
    sections[extra.section] = [
        st.Page(extra.render, title=extra.title, icon=extra.icon,
                url_path=extra.key)
    ]

current = st.navigation(sections, position="sidebar", expanded=True)

scoring.tally_sidebar()
st.sidebar.divider()
st.sidebar.caption("Cambridge IGCSE Statistics 0479. Marked to the conventions "
                   "used in the specimen papers and the O Level 4040 mark schemes.")

current.run()
