"""The feedback form, which lives outside the app.

The form is hosted by Tally, so this page is only a frame around it. Three
things here are easier to get wrong than they look.

st.iframe cannot measure a page from another origin, because the browser
forbids reading a cross-origin document, so a height of "content" quietly
becomes 400px. This form has four fields including a file upload, and 400px
cuts it in half, so the height is stated instead.

A frame that fails to load leaves a blank space and no way forward. A school
network blocking an unfamiliar domain is likely enough to plan for, so the page
offers the form as an ordinary link as well.

The form asks for an e-mail address, optionally. The page says so, because a
student should know what is being asked of them before they fill in a box.
"""

import streamlit as st

from .core import ui

FORM_ID = "rDBXKM"

# Tally's embed address rather than the form's own page, with Tally's heading
# turned off because this page already carries one. The form's own background
# is kept rather than made transparent: it is styled dark on purpose, and
# without it the fields would sit on nothing.
EMBED = (f"https://tally.so/embed/{FORM_ID}"
         "?alignLeft=1&hideTitle=1&dynamicHeight=1")
DIRECT = f"https://tally.so/r/{FORM_ID}"

HEIGHT = 959


def render() -> None:
    ui.inject()
    st.header("Report an issue or an idea")
    st.caption("If something is broken, or something would make this easier to "
               "use, please let us know here. The e-mail box is "
               "optional, and you only need it if you want a reply.")
    st.iframe(EMBED, height=HEIGHT, alt="Statonaut feedback form")
    st.caption(f"Form not loading? [Open it in a new tab]({DIRECT}).")
