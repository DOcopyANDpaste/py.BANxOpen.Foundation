"""The gate-rule seam every rule pipeline is built from."""

from typing import Protocol


class GateRule[C, O](Protocol):
    """Decides whether an action is allowed, blocked, or needs user confirmation.

    Implement this to add a business rule without touching the planner or any other rule. A plain class with
    `rule_id` and `order` attributes and an `evaluate` method satisfies it.
    """

    @property
    def rule_id(self) -> str: ...

    @property
    def order(self) -> int:
        """Evaluation order, ascending. Leave gaps (100, 200, ...) so new rules can be inserted without renumbering."""
        ...

    def evaluate(self, context: C, /) -> O: ...
