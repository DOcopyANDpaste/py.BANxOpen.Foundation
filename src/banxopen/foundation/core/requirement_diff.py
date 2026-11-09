"""What a refresh has to do to turn the requirements a part holds into the ones a domain wants."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from banxopen.foundation.core.requirement_naming import Identity, requirement_name
from banxopen.foundation.model.requirements import (
    EqualsValueRule,
    RequirementRule,
    RequirementSpec,
    SetOfValuesRule,
)
from banxopen.foundation.text import FoundationText


@dataclass(frozen=True, slots=True)
class RequirementDiff:
    """Pure, so the store's bookkeeping is tested without NX.

    Fields:
        to_create: wanted, and not in the part.
        to_replace: (existing, wanted) pairs in the part but no longer as wanted. Replaced (deleted and re-created)
            rather than edited: that keeps the store to two NX operations whose undo behaviour is known.
        to_delete: in the part, and no longer wanted.
        errors: why the wanted set cannot be written (identities that collapse to the same NX name). Nothing should
            be written when this is non-empty.
    """

    to_create: tuple[RequirementSpec, ...]
    to_replace: tuple[tuple[RequirementSpec, RequirementSpec], ...]
    to_delete: tuple[RequirementSpec, ...]
    errors: tuple[str, ...]

    @property
    def is_empty(self) -> bool:
        return not self.to_create and not self.to_replace and not self.to_delete

    @staticmethod
    def compute(
        existing: Sequence[RequirementSpec],
        wanted: Sequence[RequirementSpec],
        text: FoundationText | None = None,
    ) -> RequirementDiff:
        """`text` words the name-conflict errors; `FoundationText.DEFAULT` when None."""
        text = text or FoundationText.DEFAULT

        by_name: dict[str, list[RequirementSpec]] = {}
        for spec in wanted:
            by_name.setdefault(requirement_name(spec), []).append(spec)
        errors = tuple(
            text.requirement_name_claimed(name, (f"{s.domain}/{s.key}/{s.aspect}" for s in group))
            for name, group in by_name.items()
            if len(group) > 1
        )
        if errors:
            return RequirementDiff((), (), (), errors)

        # Matched by identity, not by NX name: a spec read back from a part carries no name_stem, so its name can
        # differ from the wanted one for the very same requirement. Renaming one otherwise unchanged is the store's job.
        existing_groups: dict[Identity, list[RequirementSpec]] = {}
        for spec in existing:
            existing_groups.setdefault(_identity(spec), []).append(spec)
        wanted_identities = {_identity(s) for s in wanted}

        to_create: list[RequirementSpec] = []
        to_replace: list[tuple[RequirementSpec, RequirementSpec]] = []
        for spec in wanted:
            group = existing_groups.get(_identity(spec))
            if group is None:
                to_create.append(spec)
            elif not _are_equivalent(group[0], spec):
                to_replace.append((group[0], spec))

        # Unwanted identities go entirely. A wanted one the part holds more than once (a hand-copied requirement, say)
        # keeps only the first, which the lookup above compared against.
        to_delete: list[RequirementSpec] = []
        for identity, group in existing_groups.items():
            to_delete.extend(group[1:] if identity in wanted_identities else group)

        return RequirementDiff(tuple(to_create), tuple(to_replace), tuple(to_delete), ())


def _identity(spec: RequirementSpec) -> Identity:
    return spec.domain, spec.key, spec.aspect


def _are_equivalent(a: RequirementSpec, b: RequirementSpec) -> bool:
    """Whether two specs would leave the same thing in NX, the name aside. Value lists compare in order (the order is
    what NX shows), while associated objects compare as a set, since NX does not keep their order."""
    return (
        _identity(a) == _identity(b)
        and a.value_type == b.value_type
        and a.severity == b.severity
        and a.checked_formula == b.checked_formula
        and _rules_equal(a.rule, b.rule)
        and tuple(a.description) == tuple(b.description)
        and set(a.associated_object_keys) == set(b.associated_object_keys)
    )


def _rules_equal(a: RequirementRule, b: RequirementRule) -> bool:
    match a, b:
        case SetOfValuesRule(), SetOfValuesRule():
            return tuple(a.values) == tuple(b.values)
        case EqualsValueRule(), EqualsValueRule():
            return _nearly_equal(a.value, b.value) and _nearly_equal(a.tolerance, b.tolerance)
        case _:
            return False


def _nearly_equal(x: float, y: float) -> bool:
    # NX hands numbers back through a string field; a round trip may differ in the last bits.
    return abs(x - y) <= 1e-9 * max(1.0, abs(x), abs(y))
