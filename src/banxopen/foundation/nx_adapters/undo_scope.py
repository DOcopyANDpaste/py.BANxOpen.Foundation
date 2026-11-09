"""Standardised undo-mark wrapper: rollback is automatic unless `commit()` is reached."""

# NX 2412's Python stubs declare instance methods without `self`, type enum members as int and give collections
# no __iter__; these rules would only report those stub defects here. Everything else is still checked.
# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportReturnType=false
# pyright: reportCallIssue=false, reportGeneralTypeIssues=false

import logging
from types import TracebackType

import NXOpen

from banxopen.foundation.nx_adapters.errors import nx_error_detail

_log = logging.getLogger(__name__)


class UndoScope:
    """Use with `with`: any exception or early exit before `commit()` rolls the part back to the mark.

    `UndoToMark`'s second parameter is the mark name and must be the same name passed to `SetUndoMark`, so it is kept.

        with UndoScope(ctx.session, "Apply Material Assignment") as undo:
            ...
            undo.commit()
    """

    def __init__(self, session: NXOpen.Session, name: str) -> None:
        self._session = session
        self._name = name
        self._mark: int | None = None
        self._committed = False

    def __enter__(self) -> UndoScope:
        self._mark = self._session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, self._name)
        return self

    def commit(self) -> None:
        self._committed = True

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        if not self._committed and self._mark is not None:
            try:
                self._session.UndoToMark(self._mark, self._name)
            except NXOpen.NXException as ex:
                _log.error("Undo to mark '%s' failed: %s", self._name, nx_error_detail(ex))
        return False  # never swallow the exception
