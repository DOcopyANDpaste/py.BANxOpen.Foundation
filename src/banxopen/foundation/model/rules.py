"""The shape every gate rule's verdict takes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum


class RuleDecision(Enum):
    ALLOW = "Allow"
    BLOCK = "Block"
    REQUIRE_CONFIRMATION = "RequireConfirmation"
    WARN = "Warn"
    """Allowed to proceed (behaves like ALLOW for planning and short-circuiting), but the message is surfaced to the
    user as a non-blocking, advisory warning."""


def _no_args() -> Mapping[str, str]:
    return {}


@dataclass(frozen=True, slots=True)
class RuleOutcome:
    """One rule's verdict.

    Fields:
        reason_code: the stable code tools branch on: the contract, not the wording.
        message: the canonical wording, built from the producing library's describer. Every tool shows it as-is.
        args: the values `message` was built from, already formatted for display, keyed by name: for a tool that
            shows them in its own layout, and for diagnostics.
        inner: the separate outcomes this one stands for, when a rule folds several into one. Empty for a single
            outcome.
    """

    rule_id: str
    decision: RuleDecision
    reason_code: str | None
    message: str | None
    args: Mapping[str, str] = field(default_factory=_no_args)
    inner: tuple[RuleOutcome, ...] = ()
