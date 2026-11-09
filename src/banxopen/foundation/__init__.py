"""BANxOpen Foundation: pure public API. Safe to import without NX.

NX operations are in `banxopen.foundation.nx`; the Block UI kit is in `banxopen.foundation.ui`.
"""

from banxopen.foundation.codes import FoundationCodes
from banxopen.foundation.core.gate_rule import GateRule
from banxopen.foundation.core.requirement_diff import RequirementDiff
from banxopen.foundation.core.requirement_store import PartRequirementStore
from banxopen.foundation.model.bodies import BodyInfo, BodyKind
from banxopen.foundation.model.ids import BodyId
from banxopen.foundation.model.requirements import (
    EqualsValueRule,
    RequirementRead,
    RequirementRule,
    RequirementSeverity,
    RequirementSpec,
    RequirementStatus,
    RequirementValueType,
    SetOfValuesRule,
    StoredRequirement,
)
from banxopen.foundation.model.results import OperationResult
from banxopen.foundation.model.rules import RuleDecision, RuleOutcome
from banxopen.foundation.text import FoundationText

__version__ = "1.1.0"

__all__ = [
    "BodyId",
    "BodyInfo",
    "BodyKind",
    "EqualsValueRule",
    "FoundationCodes",
    "FoundationText",
    "GateRule",
    "OperationResult",
    "PartRequirementStore",
    "RequirementDiff",
    "RequirementRead",
    "RequirementRule",
    "RequirementSeverity",
    "RequirementSpec",
    "RequirementStatus",
    "RequirementValueType",
    "RuleDecision",
    "RuleOutcome",
    "SetOfValuesRule",
    "StoredRequirement",
    "__version__",
]
