"""Stable codes Foundation puts on a failed `OperationResult.error_code`."""

from typing import Final


class FoundationCodes:
    """Codes, not wording, are the contract: tools branch on these and show the message as-is. The wording is
    `FoundationText`'s."""

    NO_ACTIVE_SESSION: Final = "NO_ACTIVE_SESSION"
    NO_WORK_PART: Final = "NO_WORK_PART"
    SESSION_UNAVAILABLE: Final = "SESSION_UNAVAILABLE"
    """NX raised while the session context was being resolved; the message carries the NX error."""
    REQUIREMENT_WRONG_DOMAIN: Final = "REQUIREMENT_WRONG_DOMAIN"
    REQUIREMENTS_UNREADABLE: Final = "REQUIREMENTS_UNREADABLE"
    """Also used by BANxOpen.SheetMetal when a part's requirements cannot be read."""
    REQUIREMENT_NAME_CONFLICT: Final = "REQUIREMENT_NAME_CONFLICT"
    REQUIREMENT_WRITE_FAILED: Final = "REQUIREMENT_WRITE_FAILED"
    """Also used by BANxOpen.SheetMetal when the requirements could not be written."""
    CANCELLED: Final = "CANCELLED"
    """The user declined a confirmation the library asked for (ui-kit `run_with_confirmation`)."""
