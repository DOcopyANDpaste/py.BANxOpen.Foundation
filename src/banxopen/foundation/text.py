"""The wording of every message the Foundation libraries can put in front of a user."""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar


class FoundationText:
    """Default text a tool may override (the describer pattern): one overridable member per message, and a
    `DEFAULT` instance. Code that produces one of these messages takes a `FoundationText | None` and falls back to
    `DEFAULT`. Log lines are not user text and are not here.

    Parameters that carry an NX error are already formatted (`NxDialogText.nx_error`): Core has no NXOpen.
    """

    DEFAULT: ClassVar[FoundationText]

    # ---- Session ----

    @property
    def no_active_session(self) -> str:
        return "No active NX session."

    @property
    def no_work_part(self) -> str:
        return "No active work part. Open a part before launching this tool."

    # ---- Requirements ----

    def requirements_wrong_domain(self, names: Iterable[str], domain: str) -> str:
        return f"Requirements {', '.join(names)} do not belong to domain '{domain}'."

    def requirements_unreadable(self, errors: Iterable[str]) -> str:
        return " ".join(errors)

    def requirement_name_conflict(self, errors: Iterable[str]) -> str:
        return " ".join(errors)

    def requirement_write_failed(self, nx_detail: str) -> str:
        return nx_detail

    def requirements_not_listed(self, nx_detail: str) -> str:
        return f"The part's requirements could not be listed: {nx_detail}"

    def requirement_unreadable(self, name: str, nx_detail: str) -> str:
        return f"Requirement '{name}' could not be read: {nx_detail}"

    def requirement_value_unreadable(self, name: str, detail: str) -> str:
        return f"Requirement '{name}' holds a value that could not be read: {detail}"

    def requirement_name_claimed(self, name: str, identities: Iterable[str]) -> str:
        return f"Requirement name '{name}' is claimed by {', '.join(identities)}."

    # ---- Confirmations ----

    @property
    def cancelled_by_user(self) -> str:
        return "Cancelled."

    # ---- Shared ----

    def _with_details(self, text: str, detail: str | None) -> str:
        """A worded sentence with the technical detail that caused it below, or the sentence alone."""
        return text if detail is None or not detail.strip() else f"{text}\n\nDetails: {detail}"


FoundationText.DEFAULT = FoundationText()
