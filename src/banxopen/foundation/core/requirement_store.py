"""The port a domain uses to read and write its requirements in the work part."""

from collections.abc import Sequence
from typing import Protocol

from banxopen.foundation.model.requirements import RequirementRead, RequirementSpec
from banxopen.foundation.model.results import OperationResult


class PartRequirementStore(Protocol):
    """Reads and writes the requirements a domain holds in the work part.

    The NX implementation (`banxopen.foundation.nx.create_requirement_store`) writes native NX Requirements and
    Requirement Checks, so NX itself re-evaluates them on every change, including changes made with no BANxOpen tool
    loaded. A domain only ever sees and touches its own requirements (`RequirementSpec.domain`).
    """

    def read(self, domain: str) -> RequirementRead:
        """Everything `domain` holds in the part, with NX's last verdict on each."""
        ...

    def refresh(self, domain: str, current: Sequence[RequirementSpec]) -> OperationResult[None]:
        """Makes the part hold exactly `current` for `domain`: missing ones are created, changed ones replaced, and
        the domain's requirements not in the list deleted with their checks.

        Callers run this inside their own `UndoScope`: a failure part-way leaves the part half-written, and only the
        caller's rollback puts it back. Never refresh from a failed read: an empty list deletes everything the domain
        owns. Kept requirements are renamed to the current naming, and every check is evaluated.
        """
        ...

    def audit(self, domain: str) -> Sequence[str]:
        """Diagnostic: one line per requirement `domain` owns, naming every object its check holds and whether it is
        still alive."""
        ...
