"""The real `Messenger`: NX message boxes."""

# NX 2412's Python stubs declare instance methods without `self`, type enum members as int and give collections
# no __iter__; these rules would only report those stub defects here. Everything else is still checked.
# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportReturnType=false
# pyright: reportCallIssue=false, reportGeneralTypeIssues=false

from __future__ import annotations

from typing import Any

import NXOpen

from banxopen.foundation.model.results import OperationResult
from banxopen.foundation.nx_adapters.dialog_text import NxDialogText

_YES = 1
"""`NXMessageBox.Show` with DialogType.Question returns 1 for yes, 2 for no (NX 2412 stub documentation)."""


class NxMessenger:
    """Message boxes with `NxDialogText` titles, or one `title` for every box when given. A failed result's message
    is the library's own wording and is shown as-is."""

    def __init__(self, title: str | None = None, text: NxDialogText | None = None) -> None:
        self._title = title
        self._text = text or NxDialogText.DEFAULT

    def show_result(self, result: OperationResult[Any], success_message: str | None = None) -> None:
        if result.ok:
            message = success_message or result.message
            if message:
                self._show(self._title or self._text.success_title, NXOpen.NXMessageBox.DialogType.Information, message)
            return
        self.show_error(result.message or self._text.nx_refused_the_change(None))

    def ask(self, question: str) -> bool:
        return (
            self._show(self._title or self._text.confirm_title, NXOpen.NXMessageBox.DialogType.Question, question)
            == _YES
        )

    def show_error(self, message: str) -> None:
        self._show(self._title or self._text.error_title, NXOpen.NXMessageBox.DialogType.Error, message)

    def show_info(self, title: str, message: str) -> None:
        """Something that is neither a failure nor a question: chiefly a choice a rule made on the user's behalf."""
        self._show(title, NXOpen.NXMessageBox.DialogType.Information, message)

    @staticmethod
    def _show(title: str, kind: NXOpen.NXMessageBox.DialogType, message: str) -> int:
        return NXOpen.UI.GetUI().NXMessageBox.Show(title, kind, message)
