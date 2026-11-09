"""Reading the app's teaching text off disk.

Every word a student reads lives in a Markdown file under `content/<topic>/`,
and every question in a `.toml` file beside it, so the wording can be changed
without touching any Python. Files are read on each rerun rather than cached,
so an edit shows up as soon as the page is reloaded.

No Streamlit import here: a page decides how to report a problem, this module
only finds, reads and splits the files.
"""

import pathlib
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

try:                                     # Python 3.11 and newer
    import tomllib
except ModuleNotFoundError:              # pragma: no cover - older interpreters
    try:
        import tomli as tomllib          # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None                   # type: ignore[assignment]


class ContentError(Exception):
    """Something is missing or malformed in a content file."""


def content_root() -> pathlib.Path:
    """The `content/` folder at the top of the project."""
    here = pathlib.Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "content"
        if candidate.is_dir():
            return candidate
    raise ContentError(
        "Cannot find the 'content' folder. It should sit next to streamlit_app.py."
    )


def slug(text: str) -> str:
    """A stable key for a heading, so wording changes but spacing does not."""
    return re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-")


@dataclass
class Document:
    """A Markdown file split on its `##` headings."""

    path: pathlib.Path
    title: str = ""
    intro: str = ""
    bodies: Dict[str, str] = field(default_factory=dict)
    headings: Dict[str, str] = field(default_factory=dict)

    def section(self, key: str) -> str:
        if key not in self.bodies:
            raise ContentError(
                f"{self.path.name} has no '## ' heading that reads as '{key}'. "
                f"It has: {', '.join(self.bodies) or 'none'}. "
                "Keep the headings as they are, or update the page that reads them."
            )
        return self.bodies[key]

    def has(self, key: str) -> bool:
        return key in self.bodies


def parse(text: str, path: pathlib.Path) -> Document:
    doc = Document(path=path)
    current: Optional[str] = None
    intro: List[str] = []
    buffer: List[str] = []

    def flush() -> None:
        if current is not None:
            doc.bodies[current] = "\n".join(buffer).strip()

    for line in text.splitlines():
        if line.startswith("# ") and not doc.title and current is None:
            doc.title = line[2:].strip()
            continue
        if line.startswith("## "):
            flush()
            heading = line[3:].strip()
            current = slug(heading)
            doc.headings[current] = heading
            buffer = []
            continue
        (buffer if current is not None else intro).append(line)
    flush()
    doc.intro = "\n".join(intro).strip()
    return doc


class Library:
    """The content files belonging to one topic."""

    def __init__(self, topic: str, root: Optional[pathlib.Path] = None) -> None:
        self.topic = topic
        self._root = root

    @property
    def directory(self) -> pathlib.Path:
        folder = (self._root or content_root()) / self.topic
        if not folder.is_dir():
            raise ContentError(f"No content folder for '{self.topic}' at {folder}.")
        return folder

    def path(self, name: str, suffix: str = ".md") -> pathlib.Path:
        file = self.directory / f"{name}{suffix}"
        if not file.is_file():
            raise ContentError(
                f"Missing {file.name} in content/{self.topic}/. "
                f"Files there now: {', '.join(sorted(p.name for p in self.directory.iterdir()))}"
            )
        return file

    def text(self, name: str) -> str:
        """A whole Markdown file, ready for st.markdown."""
        return self.path(name).read_text(encoding="utf-8").strip()

    def document(self, name: str) -> Document:
        """A Markdown file split into its sections."""
        file = self.path(name)
        return parse(file.read_text(encoding="utf-8"), file)

    def data(self, name: str) -> dict:
        """A TOML file."""
        if tomllib is None:                            # pragma: no cover
            raise ContentError(
                "Reading .toml needs Python 3.11 or newer, or the 'tomli' package."
            )
        file = self.path(name, ".toml")
        try:
            return tomllib.loads(file.read_text(encoding="utf-8"))
        except Exception as exc:                       # noqa: BLE001
            raise ContentError(f"{file.name} is not valid TOML: {exc}") from exc

    def files(self) -> List[str]:
        return sorted(p.name for p in self.directory.iterdir() if p.is_file())
