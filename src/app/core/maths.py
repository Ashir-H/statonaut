"""Mathematical notation, written in one place so it renders the same everywhere.

Streamlit's markdown hands anything between single dollars to KaTeX, so a
formula can sit inside a sentence. Two rules it imposes, both easy to trip
over: an expression may not begin or end with a space just inside the dollars,
and the closing dollar may not be followed by a digit.

No Streamlit import here - these are strings, and they are built the same way
whether they end up in a caption, a model answer or a content file.
"""

from typing import Optional, Sequence


def inline(expression: str) -> str:
    """A formula for the middle of a sentence."""
    return f"${expression.strip()}$"


def words(text: str) -> str:
    """Words inside a formula, upright rather than italic."""
    return rf"\text{{{text}}}"


def fraction(top, bottom) -> str:
    return rf"\frac{{{top}}}{{{bottom}}}"


def share(size, population, sample, result: Optional[int] = None) -> str:
    """A stratum's share: its size over the population, times the sample."""
    expression = rf"{fraction(size, population)} \times {sample}"
    return expression if result is None else rf"{expression} = {result}"


def quotient(top, bottom, result=None) -> str:
    expression = fraction(top, bottom)
    return expression if result is None else rf"{expression} = {result}"


def joined(expressions: Sequence[str], separator: str = ", ") -> str:
    """Several formulas in a row, each its own expression.

    Not one expression with punctuation inside it: KaTeX would set the commas
    as mathematics.
    """
    return separator.join(inline(e) for e in expressions)
