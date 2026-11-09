from banxopen.foundation.nx import NxDialogText, nx_error_code, nx_error_detail


class FakeNxError(Exception):
    def __init__(self, code: int | None, message: str) -> None:
        super().__init__(message)
        if code is not None:
            self.ErrorCode = code
        self._message = message

    def GetMessage(self) -> str:  # noqa: N802
        return self._message


def test_dialog_text_matches_the_csharp_wording():
    text = NxDialogText.DEFAULT

    assert (text.error_title, text.confirm_title, text.success_title) == ("Error", "Confirm", "Success")
    assert text.could_not_start("Bead", None) == "Bead could not start."
    assert text.could_not_start("Bead", "No part.") == "Bead could not start.\n\nDetails: No part."
    assert text.nx_refused_the_change("  ") == "NX refused the change."
    assert text.handler_failed("Apply", "boom") == (
        "An error occurred handling 'Apply':\nboom\n\nFull details were written to the Listing Window."
    )


def test_nx_errors_read_the_code_when_present_and_degrade_when_not():
    with_code = FakeNxError(3520016, "Invalid tag")
    without_code = FakeNxError(None, "Odd")

    assert nx_error_detail(with_code) == "NX 3520016: Invalid tag"  # type: ignore[arg-type]
    assert nx_error_code(with_code) == "NX-3520016"  # type: ignore[arg-type]
    assert nx_error_detail(without_code) == "NX ?: Odd"  # type: ignore[arg-type]
    assert nx_error_code(without_code) == "NX-UNKNOWN"  # type: ignore[arg-type]
