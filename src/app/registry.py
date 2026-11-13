"""What the app contains.

Every topic is a package under `app.topics` that exposes a `TOPIC`. The
sidebar, the home page and the tests are all built from this list, so adding a
topic means writing the topic and adding one line here - nothing else.
"""

from dataclasses import dataclass
from typing import Callable, List, Tuple


@dataclass(frozen=True)
class Page:
    """One page of one topic."""

    key: str                      # unique within the topic; becomes part of the URL
    title: str                    # what the sidebar shows
    render: Callable[[], None]    # draws the page
    icon: str = ""                # a material icon, e.g. ":material/school:"
    blurb: str = ""               # one line, used on the home page


@dataclass(frozen=True)
class Topic:
    key: str                      # unique; becomes part of the URL
    title: str                    # "Random number tables"
    unit: str                     # "Unit 1"
    unit_title: str               # "Data and its collection"
    syllabus: str                 # "1.2 and 1.4"
    summary: str
    pages: Tuple[Page, ...]

    @property
    def section(self) -> str:
        """The sidebar heading this topic's pages sit under."""
        return f"{self.unit} · {self.title}"

    @property
    def line(self) -> str:
        return f"{self.unit} · {self.unit_title} · syllabus {self.syllabus}"

    def page(self, key: str) -> Page:
        return next(p for p in self.pages if p.key == key)


@dataclass(frozen=True)
class Standalone:
    """A page belonging to no topic: it teaches nothing and has no unit.

    Listed here for the same reason the topics are: so that a page cannot
    appear in the sidebar without the addresses and the tests knowing about it.
    """

    key: str                      # unique; becomes the whole address
    section: str                   # the sidebar heading it sits under
    title: str
    render: Callable[[], None]
    icon: str = ""


def standalone() -> List[Standalone]:
    """Every page that is not part of a topic."""
    from .form import render as feedback

    return [
        Standalone(key="submit-feedback",
                   section="Report an issue or an idea",
                   title="Submit feedback",
                   render=feedback,
                   icon=":material/feedback:"),
    ]


def topics() -> List[Topic]:
    """Every topic in the app, in teaching order."""
    from .topics.central_tendency.topic import TOPIC as central_tendency
    from .topics.sampling.topic import TOPIC as sampling

    return [sampling, central_tendency]


def pages() -> List[Tuple[Topic, Page]]:
    return [(t, p) for t in topics() for p in t.pages]


def url_path(topic: Topic, page: Page) -> str:
    """The page's own address.

    Streamlit does not support nested pathnames (issue #8971), so the two
    levels are joined with an underscore: /sampling_drill, not /sampling/drill.
    """
    return f"{topic.key}_{page.key}"
