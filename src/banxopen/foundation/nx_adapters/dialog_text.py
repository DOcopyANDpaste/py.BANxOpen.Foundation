"""Wording every NX dialog built on Foundation shows the same way, with no domain meaning."""

from typing import TYPE_CHECKING, ClassVar

from banxopen.foundation.nx_adapters.errors import nx_error_detail

if TYPE_CHECKING:
    import NXOpen


class NxDialogText:
    """Message box titles, start-up and unexpected-error messages, and how an NX error is put in front of a user.

    Default text a tool may override, like the library describers (`FoundationText`, ...); a tool's own wording is in
    its `text` module.
    """

    DEFAULT: ClassVar[NxDialogText]

    # ---- Message box titles ----

    @property
    def error_title(self) -> str:
        return "Error"

    @property
    def confirm_title(self) -> str:
        return "Confirm"

    @property
    def success_title(self) -> str:
        return "Success"

    # ---- Messages ----

    def could_not_start(self, tool: str, detail: str | None) -> str:
        """`tool` is the tool's name as the user knows it; `detail` why, as the session check or lower layer said."""
        return self._with_details(f"{tool} could not start.", detail)

    def handler_failed(self, what: str, detail: str) -> str:
        """A dialog callback raised. The full traceback is written to the Listing Window by the ui-kit."""
        return f"An error occurred handling '{what}':\n{detail}\n\nFull details were written to the Listing Window."

    def nx_refused_the_change(self, detail: str | None) -> str:
        """A failed operation that came with no message of its own."""
        return self._with_details("NX refused the change.", detail)

    def nx_error(self, ex: NXOpen.NXException) -> str:
        """An NX error as shown to a user, under a worded sentence."""
        return nx_error_detail(ex)

    def _with_details(self, text: str, detail: str | None) -> str:
        return text if detail is None or not detail.strip() else f"{text}\n\nDetails: {detail}"


NxDialogText.DEFAULT = NxDialogText()
