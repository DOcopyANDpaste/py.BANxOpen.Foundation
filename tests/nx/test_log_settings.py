import logging

import pytest

from banxopen.foundation.nx import LogSettings, LogTarget, NxLogHandler


@pytest.mark.parametrize(
    ("target_text", "expected"),
    [
        (None, LogTarget.NX_LOG),
        ("", LogTarget.NX_LOG),
        ("ListingWindow", LogTarget.LISTING_WINDOW),
        ("  both ", LogTarget.BOTH),
        ("NXLOG", LogTarget.NX_LOG),
        ("1", LogTarget.LISTING_WINDOW),  # C# Enum.TryParse accepts the numeric value too
        ("7", LogTarget.NX_LOG),
        ("console", LogTarget.NX_LOG),
    ],
)
def test_target_parses_like_the_csharp_log(target_text, expected):
    from banxopen.foundation.nx_adapters.nx_logging import parse_log_settings

    assert parse_log_settings(target_text, None).target is expected


@pytest.mark.parametrize(
    ("debug_text", "expected"),
    [(None, False), ("", False), ("1", True), (" TRUE ", True), ("On", True), ("yes", False), ("0", False)],
)
def test_debug_flag_parses_like_the_csharp_log(debug_text, expected):
    from banxopen.foundation.nx_adapters.nx_logging import parse_log_settings

    assert parse_log_settings(None, debug_text).debug is expected


class FakeListingWindow:
    def __init__(self) -> None:
        self.IsOpen = False
        self.lines: list[str] = []

    def Open(self) -> None:  # noqa: N802
        self.IsOpen = True

    def WriteLine(self, line: str) -> None:  # noqa: N802
        self.lines.append(line)


class FakeLogFile:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def WriteLine(self, line: str) -> None:  # noqa: N802
        self.lines.append(line)


class FakeSession:
    def __init__(self) -> None:
        self.ListingWindow = FakeListingWindow()
        self.LogFile = FakeLogFile()


def _emit(settings: LogSettings, level: int, message: str) -> FakeSession:
    session = FakeSession()
    handler = NxLogHandler(session, settings)  # type: ignore[arg-type]  # duck-typed fake session
    handler.emit(logging.LogRecord("banxopen.test", level, __file__, 1, message, None, None))
    return session


def test_syslog_lines_are_prefixed_and_split_per_line():
    session = _emit(LogSettings(LogTarget.NX_LOG), logging.WARNING, "first\r\nsecond")

    assert session.LogFile.lines == ["[BANxOpen][WARN] first", "[BANxOpen][WARN] second"]
    assert session.ListingWindow.lines == []


def test_listing_window_gets_the_whole_message_unprefixed():
    session = _emit(LogSettings(LogTarget.LISTING_WINDOW), logging.ERROR, "a\nb")

    assert session.ListingWindow.IsOpen
    assert session.ListingWindow.lines == ["[ERROR] a\nb"]
    assert session.LogFile.lines == []


@pytest.mark.parametrize(("debug", "listed"), [(False, 0), (True, 1)])
def test_debug_always_reaches_the_syslog_and_the_listing_window_only_when_on(debug, listed):
    session = _emit(LogSettings(LogTarget.LISTING_WINDOW, debug=debug), logging.DEBUG, "detail")

    assert session.LogFile.lines == ["[BANxOpen][DEBUG] detail"]
    assert len(session.ListingWindow.lines) == listed
