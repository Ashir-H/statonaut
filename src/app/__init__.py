"""Statonaut - practice app for Cambridge IGCSE Statistics 0479."""

__all__ = ["registry", "home", "core", "topics", "main"]


def main() -> None:
    """Launch the app, so `uv run stats101` works as well as `streamlit run`."""
    import pathlib
    import sys

    from streamlit.web import cli

    entry = pathlib.Path(__file__).resolve().parents[2] / "streamlit_app.py"
    sys.argv = ["streamlit", "run", str(entry)]
    sys.exit(cli.main())
