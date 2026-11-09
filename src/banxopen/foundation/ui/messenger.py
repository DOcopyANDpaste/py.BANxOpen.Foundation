"""How presenters talk to the user, as a seam tests can fake. Pure: no NXOpen."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, TypeVar

from banxopen.foundation.codes import FoundationCodes
from banxopen.foundation.model.results import OperationResult
from banxopen.foundation.text import FoundationText

T = TypeVar("T")


class Messenger(Protocol):
    def show_result(self, result: OperationResult[Any], success_message: str | None = None) -> None:
        """A failed result's message as an error; a successful one's (or `success_message`) as information."""
        ...

    def ask(self, question: str) -> bool:
        """A yes/no question. True for yes."""
        ...


def run_with_confirmation(
    messenger: Messenger,
    operation: Callable[[bool], OperationResult[T]],
    text: FoundationText | None = None,
) -> OperationResult[T]:
    """Call `operation(False)`; if the library asks for confirmation, put its question to the user and call again
    with `True`. Declining returns a CANCELLED failure. New confirmation rules in a library need no tool change."""
    result = operation(False)
    if result.needs_confirmation:
        if not messenger.ask(result.question or ""):
            return OperationResult.fail(FoundationCodes.CANCELLED, (text or FoundationText.DEFAULT).cancelled_by_user)
        result = operation(True)
    return result
