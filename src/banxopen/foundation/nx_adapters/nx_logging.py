"""Routing the `banxopen.*` loggers into NX: the syslog, the Listing Window, or both.

`print` is invisible inside NX. Library code only calls `logging.getLogger(__name__)`; entry points call
`install_nx_logging` (interactive) or `install_batch_logging` (run_journal) once. Settings come from the
environment, so a user or site sets them in ugii_env or Windows without touching any tool's config:

- `BANXOPEN_LOG_TARGET` = `NxLog` (default) | `ListingWindow` | `Both`
- `BANXOPEN_DEBUG` = `1` | `true` | `on` to show debug lines in the Listing Window (default off)

Debug lines always go to the syslog, and to the Listing Window only when debug is on.
"""

# NX 2412's Python stubs declare instance methods without `self`, type enum members as int and give collections
# no __iter__; these rules would only report those stub defects here. Everything else is still checked.
# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportReturnType=false
# pyright: reportCallIssue=false, reportGeneralTypeIssues=false

from __future__ import annotations

import logging
import os
import re
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import NXOpen

TARGET_VARIABLE = "BANXOPEN_LOG_TARGET"
DEBUG_VARIABLE = "BANXOPEN_DEBUG"
ROOT_LOGGER = "banxopen"

_PREFIX = "[BANxOpen]"
_LINE_BREAK = re.compile(r"\r\n|\n")
_log = logging.getLogger(__name__)


class LogTarget(Enum):
    NX_LOG = "NxLog"
    """The NX session log (syslog, Help > Log File). The default."""
    LISTING_WINDOW = "ListingWindow"
    BOTH = "Both"


@dataclass(frozen=True, slots=True)
class LogSettings:
    target: LogTarget = LogTarget.NX_LOG
    debug: bool = False


def parse_log_settings(target_text: str | None, debug_text: str | None) -> LogSettings:
    """Settings from the two variables' raw values. A missing or unrecognised target falls back to NxLog.

    Matches the C# parse: names are case-insensitive and trimmed, and the numeric values 0-2 are accepted too.
    """
    raw = (target_text or "").strip()
    members = list(LogTarget)
    target = next((t for t in members if t.value.casefold() == raw.casefold()), None)
    if target is None and raw.isdigit() and int(raw) < len(members):
        target = members[int(raw)]
    flag = (debug_text or "").strip().casefold()
    return LogSettings(target or LogTarget.NX_LOG, flag in ("1", "true", "on"))


_LEVEL_NAMES = {logging.DEBUG: "DEBUG", logging.INFO: "INFO", logging.WARNING: "WARN"}


def _level_name(levelno: int) -> str:
    return _LEVEL_NAMES.get(levelno, "ERROR" if levelno >= logging.ERROR else "INFO")


class NxLogHandler(logging.Handler):
    """Writes records to the NX syslog and/or the Listing Window in the C# tools' formats."""

    def __init__(self, session: NXOpen.Session, settings: LogSettings) -> None:
        super().__init__(logging.DEBUG)
        self._session = session
        self.settings = settings

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = _level_name(record.levelno)
            message = record.getMessage()
            if record.exc_info:
                message = f"{message}\n{logging.Formatter().formatException(record.exc_info)}"

            target = self.settings.target
            if record.levelno <= logging.DEBUG:
                to_syslog, to_listing = True, self.settings.debug
            else:
                to_syslog = target in (LogTarget.NX_LOG, LogTarget.BOTH)
                to_listing = target in (LogTarget.LISTING_WINDOW, LogTarget.BOTH)

            if to_syslog:
                # The syslog is line-oriented: each line is prefixed, so a grep for the prefix finds all of it.
                for line in _LINE_BREAK.split(message):
                    self._session.LogFile.WriteLine(f"{_PREFIX}[{level}] {line}")
            if to_listing:
                lw = self._session.ListingWindow
                if not lw.IsOpen:
                    lw.Open()
                lw.WriteLine(f"[{level}] {message}")
        except Exception:  # noqa: BLE001  (logging must never raise into NX; stdlib convention)
            self.handleError(record)


def install_nx_logging(session: NXOpen.Session) -> LogSettings:
    """Attach the NX handler to the `banxopen` logger, configured from the environment. Safe to call on every launch:
    the NX session is long-lived, so an earlier handler is replaced, not duplicated."""
    target_text = os.environ.get(TARGET_VARIABLE)
    debug_text = os.environ.get(DEBUG_VARIABLE)
    settings = parse_log_settings(target_text, debug_text)

    root = _root_logger()
    for handler in [h for h in root.handlers if isinstance(h, NxLogHandler)]:
        root.removeHandler(handler)
    root.addHandler(NxLogHandler(session, settings))

    _log.debug(
        "Log: target %s (%s='%s'), debug %s (%s='%s').",
        settings.target.value,
        TARGET_VARIABLE,
        target_text or "",
        "on" if settings.debug else "off",
        DEBUG_VARIABLE,
        (debug_text or "").strip(),
    )
    return settings


def install_batch_logging(file_name: str) -> Path:
    """For run_journal: log to `%TEMP%\\BANxOpen\\logs\\<file_name>` and the console, so a failure can be diagnosed
    after the process exits. Returns the log file path."""
    path = Path(tempfile.gettempdir()) / "BANxOpen" / "logs" / file_name
    path.parent.mkdir(parents=True, exist_ok=True)

    root = _root_logger()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    for handler in (logging.FileHandler(path, encoding="utf-8"), logging.StreamHandler()):
        handler.setFormatter(formatter)
        root.addHandler(handler)
    return path


def _root_logger() -> logging.Logger:
    # DEBUG always: debug lines must reach the syslog even when the Listing Window hides them.
    root = logging.getLogger(ROOT_LOGGER)
    root.setLevel(logging.DEBUG)
    return root
