"""Expressions a tool owns are locked against hand edits and unlocked only for the tool's own edit."""

# NX 2412's Python stubs declare instance methods without `self`, type enum members as int and give collections
# no __iter__; these rules would only report those stub defects here. Everything else is still checked.
# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportReturnType=false
# pyright: reportCallIssue=false, reportGeneralTypeIssues=false

from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import NXOpen


@contextmanager
def expression_unlocked(expression: NXOpen.Expression) -> Iterator[NXOpen.Expression]:
    """Unlock (`IsNoEdit`, the Expressions dialog's lock) for the block, then restore the previous state: an
    expression someone deliberately left unlocked stays unlocked.

        with expression_unlocked(expression):
            expressions.EditExpressionWithUnits(...)
    """
    was_locked = expression.IsNoEdit
    if was_locked:
        expression.IsNoEdit = False
    try:
        yield expression
    finally:
        if was_locked:
            expression.IsNoEdit = True


def lock_expression(expression: NXOpen.Expression) -> None:
    """Lock `expression` against hand edits."""
    expression.IsNoEdit = True
