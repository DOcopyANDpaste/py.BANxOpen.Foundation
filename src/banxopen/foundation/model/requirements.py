"""Requirements a feature domain holds in a part as native NX Requirements."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RequirementValueType(Enum):
    """What kind of value an NX Requirement compares."""

    NUMBER = "Number"
    STRING = "String"


class RequirementSeverity(Enum):
    """How loudly NX reports a failed check. Mirrors `NXOpen.Validate.RequirementBuilder.SeverityOptions`."""

    INFORMATION = "Information"
    WARNING = "Warning"
    ERROR = "Error"


@dataclass(frozen=True, slots=True)
class SetOfValuesRule:
    """The checked value must be one of `values`: NX's "set of values" definition method.

    For a STRING requirement NX compares the checked expression's value including its double quotes, so each value
    must be written quoted (`'"2024-O"'`). Values are stored and read back as given, in order.
    """

    values: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EqualsValueRule:
    """The checked value must equal `value` within `tolerance`: NX's single-sided comparison with the Equal
    operator. Values are in the part's own units."""

    value: float
    tolerance: float


RequirementRule = SetOfValuesRule | EqualsValueRule
"""The comparison a requirement makes. Closed set: the two definition methods the tools write."""


@dataclass(frozen=True, slots=True, kw_only=True)
class RequirementSpec:
    """One requirement a feature domain wants to hold in a part, written as a native NX Requirement plus the
    Requirement Check that links it to `checked_formula`.

    Identity is (`domain`, `key`, `aspect`): a domain owns every requirement it wrote, a key groups the requirements
    one source imposes (a bead SPEC, say), and the aspect tells them apart (grade, thickness). The NX name is derived
    from the identity, or from `name_stem` when the domain gives a shorter one, so it is never stored separately.

    Fields:
        domain: owning domain, e.g. "SHEETMETAL.BEAD". A store only ever touches its own domain's requirements.
        key: what imposes the requirement within the domain, e.g. "BA|B1005010-2".
        aspect: which property it constrains, e.g. "GRADE".
        checked_formula: the expression NX evaluates the requirement against.
        description: shown to the user in NX alongside the check. The store adds its own bookkeeping line and strips
            it again on read.
        associated_object_keys: the objects NX highlights for the check, as tag strings. Order-insensitive.
        name_stem: what the NX name is built from in place of domain and key. Only the name: identity stays
            (domain, key, aspect). Not read back from NX; a spec read from a part has none.
    """

    domain: str
    key: str
    aspect: str
    value_type: RequirementValueType
    rule: RequirementRule
    severity: RequirementSeverity
    checked_formula: str
    description: tuple[str, ...]
    associated_object_keys: tuple[str, ...]
    name_stem: str | None = None


class RequirementStatus(Enum):
    """NX's last verdict on a requirement's check. Mirrors `NXOpen.Validation.Result`."""

    UNKNOWN = "Unknown"
    PASS = "Pass"
    INFORMATION = "Information"
    WARNING = "Warning"
    FAILED = "Failed"
    SKIPPED = "Skipped"


@dataclass(frozen=True, slots=True)
class StoredRequirement:
    """A requirement as read back from a part, with NX's own verdict on it."""

    spec: RequirementSpec
    status: RequirementStatus


@dataclass(frozen=True, slots=True)
class RequirementRead:
    """Everything a domain owns in a part. `errors` lists what could not be read: a reader never silently drops a
    requirement it failed to understand, since a caller would then treat it as absent."""

    requirements: tuple[StoredRequirement, ...]
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors
