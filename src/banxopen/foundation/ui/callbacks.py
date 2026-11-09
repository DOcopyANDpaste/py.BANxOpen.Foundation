"""The outermost UI boundary: dialog callbacks and launches never let an error crash NX."""

# NX 2412's Python stubs declare instance methods without `self`, type enum members as int and give collections
# no __iter__; these rules would only report those stub defects here. Everything else is still checked.
# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportReturnType=false
# pyright: reportCallIssue=false, reportGeneralTypeIssues=false

from __future__ import annotations

import functools
import logging
import traceback
from collections.abc import Callable
from typing import Any, ParamSpec, Protocol

import NXOpen

from banxopen.foundation.nx_adapters.dialog_text import NxDialogText
from banxopen.foundation.ui.nx_messenger import NxMessenger

P = ParamSpec("P")
_log = logging.getLogger(__name__)


class LaunchableDialog(Protocol):
    def Launch(self) -> Any: ...  # noqa: N802  (Styler-generated name)
    def Dispose(self) -> None: ...  # noqa: N802


def ui_callback(what: str) -> Callable[[Callable[P, int]], Callable[P, int]]:
    """Decorator for a dialog callback: an unexpected error is logged, its traceback written to the Listing Window,
    and the user shown `NxDialogText.handler_failed`. The callback then returns 1 (the dialog stays open)."""

    def decorate(fn: Callable[P, int]) -> Callable[P, int]:
        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> int:
            try:
                return fn(*args, **kwargs)
            except Exception as ex:  # noqa: BLE001  (boundary: last line of defence for UI callbacks)
                _report(what, ex)
                return 1

        return wrapper

    return decorate


def launch_dialog(dialog_factory: Callable[[], LaunchableDialog], tool: str) -> None:
    """Create, launch and always dispose a Styler-generated dialog. A failure to start is shown as
    `NxDialogText.could_not_start(tool, ...)`."""
    dialog: LaunchableDialog | None = None
    try:
        dialog = dialog_factory()
        dialog.Launch()
    except Exception as ex:  # noqa: BLE001  (boundary)
        _log.exception("%s could not start", tool)
        NxMessenger().show_error(NxDialogText.DEFAULT.could_not_start(tool, str(ex)))
    finally:
        if dialog is not None:
            dialog.Dispose()


def _report(what: str, ex: Exception) -> None:
    _log.exception("An error occurred handling '%s'", what)
    try:
        lw = NXOpen.Session.GetSession().ListingWindow
        if not lw.IsOpen:
            lw.Open()
        lw.WriteLine("".join(traceback.format_exception(ex)))
    except NXOpen.NXException:
        _log.warning("The traceback could not be written to the Listing Window.")
    NxMessenger().show_error(NxDialogText.DEFAULT.handler_failed(what, str(ex)))
