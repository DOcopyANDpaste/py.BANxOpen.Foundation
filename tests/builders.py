"""Test-data builders shared across the suite (ports of the C# `RequirementNamingTests.Spec` helper)."""

from __future__ import annotations

from collections.abc import Sequence

from banxopen.foundation import (
    RequirementRule,
    RequirementSeverity,
    RequirementSpec,
    RequirementValueType,
    SetOfValuesRule,
)


def spec(
    domain: str = "D",
    key: str = "K",
    aspect: str = "A",
    rule: RequirementRule | None = None,
    description: Sequence[str] | None = None,
    objects: Sequence[str] | None = None,
    formula: str = "expr",
) -> RequirementSpec:
    return RequirementSpec(
        domain=domain,
        key=key,
        aspect=aspect,
        value_type=RequirementValueType.STRING,
        rule=rule or SetOfValuesRule(("a", "b")),
        severity=RequirementSeverity.WARNING,
        checked_formula=formula,
        description=tuple(description) if description is not None else ("line",),
        associated_object_keys=tuple(objects) if objects is not None else ("101", "102"),
    )
