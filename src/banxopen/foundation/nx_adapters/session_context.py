"""A validated snapshot of the NX environment, resolved once at the boundary."""

# NX 2412's Python stubs declare instance methods without `self`, type enum members as int and give collections
# no __iter__; these rules would only report those stub defects here. Everything else is still checked.
# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportReturnType=false
# pyright: reportCallIssue=false, reportGeneralTypeIssues=false

import logging
from dataclasses import dataclass

import NXOpen
import NXOpen.UF  # pyright: ignore[reportMissingImports]  # NX ships no UF stubs

from banxopen.foundation.codes import FoundationCodes
from banxopen.foundation.model.results import OperationResult
from banxopen.foundation.nx_adapters.dialog_text import NxDialogText
from banxopen.foundation.text import FoundationText

_log = logging.getLogger(__name__)

_SHEET_METAL_APPLICATION = "UG_APP_SBSM"
"""`Session.ApplicationName` in NX Sheet Metal (NX-internal string; logged at every launch to confirm on upgrades)."""


@dataclass(frozen=True, slots=True)
class NxSessionContext:
    """Nothing else in the adapter layer calls `Session.GetSession()` / `UFSession.GetUFSession()` directly.

    `try_initialize` hard-blocks when there is no active work part: work-part inspection happens right at dialog
    launch, so launch must stop there. `work_part` is the work part at launch, as in the C# tools.
    """

    session: NXOpen.Session
    uf: NXOpen.UF.UFSession
    ui: NXOpen.UI | None
    """None when NX runs without a UI (run_journal)."""
    work_part: NXOpen.Part
    current_application: str
    """As `Session.ApplicationName` reported it at launch. Empty when NX could not say."""

    @staticmethod
    def try_initialize(text: FoundationText | None = None) -> OperationResult[NxSessionContext]:
        """The context, or a failed result whose message says why the tool cannot start, worded for the user."""
        text = text or FoundationText.DEFAULT
        try:
            session = NXOpen.Session.GetSession()
            if session is None:
                return OperationResult.fail(FoundationCodes.NO_ACTIVE_SESSION, text.no_active_session)

            work_part = session.Parts.Work
            if work_part is None:
                return OperationResult.fail(FoundationCodes.NO_WORK_PART, text.no_work_part)

            return OperationResult.success(
                NxSessionContext(
                    session=session,
                    uf=NXOpen.UF.UFSession.GetUFSession(),
                    ui=_try_get_ui(),
                    work_part=work_part,
                    current_application=_detect_application(session),
                )
            )
        except NXOpen.NXException as ex:
            return OperationResult.fail(FoundationCodes.SESSION_UNAVAILABLE, NxDialogText.DEFAULT.nx_error(ex))

    def is_alive(self, tag: int) -> bool:
        """Whether `tag` names a live object: not deleted, condemned, temporary or never valid. For cleanup that must
        not touch an object NX already freed."""
        if not tag:
            return False
        try:
            return self.uf.Obj.AskStatus(tag) == NXOpen.UF.UFConstants.UF_OBJ_ALIVE
        except NXOpen.NXException:
            return False

    @property
    def is_sheet_metal_application(self) -> bool:
        return self.current_application.casefold() == _SHEET_METAL_APPLICATION.casefold()


def _try_get_ui() -> NXOpen.UI | None:
    try:
        return NXOpen.UI.GetUI()
    except NXOpen.NXException:
        return None


def _detect_application(session: NXOpen.Session) -> str:
    # Logged every launch: the application names are NX-internal strings, so the log is how a new NX version's names
    # get confirmed. A failure only loses application-specific behaviour, so it does not stop the tool.
    try:
        application = session.ApplicationName or ""
    except NXOpen.NXException as ex:
        _log.warning(
            "The current NX application could not be read (%s); application-specific behaviour is off.",
            NxDialogText.DEFAULT.nx_error(ex),
        )
        return ""
    _log.debug("NX application: '%s'.", application)
    return application
