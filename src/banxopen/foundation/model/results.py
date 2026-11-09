"""The result every library operation returns for an expected outcome."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")
V = TypeVar("V")


@dataclass(frozen=True, slots=True)
class OperationResult(Generic[T]):
    """Outcome of an operation a caller must show to a user.

    `value` is meaningful only when `ok` is true. `message` is user-facing wording from the producing library's
    describer and is shown as-is; `error_code` is the stable contract tools may branch on. A result with
    `needs_confirmation` asks the caller to put `question` to the user and call again confirmed.
    `OperationResult[None]` stands in for C#'s non-generic `OperationResult`.

    The factories are typed for strict callers: `success(value)` infers `OperationResult[type of value]`
    (`success()` is `OperationResult[None]`), and `fail`/`confirm` fit any `OperationResult[X]`.
    """

    ok: bool
    value: T | None = None
    error_code: str | None = None
    message: str | None = None
    needs_confirmation: bool = False
    question: str | None = None

    @staticmethod
    def success(value: V = None, message: str | None = None) -> OperationResult[V]:
        return OperationResult(True, value, None, message)

    @staticmethod
    def fail(code: str, message: str) -> OperationResult[Any]:
        return OperationResult(False, None, code, message)

    @staticmethod
    def confirm(question: str) -> OperationResult[Any]:
        return OperationResult(False, None, None, None, needs_confirmation=True, question=question)
