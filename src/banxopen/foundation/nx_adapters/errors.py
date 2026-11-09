"""Reading an `NXOpen.NXException` the same way everywhere."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import NXOpen


def nx_error_code(ex: NXOpen.NXException) -> str:
    """The NX error code, as the stable code to log and put on a failed result: `NX-<code>`.

    The NX 2412 Python stub exposes only `GetMessage()`; the binary also contains `ErrorCode`, so it is read
    defensively until scripts/validate_runtime.py confirms it.
    """
    code = getattr(ex, "ErrorCode", None)
    return f"NX-{code}" if code is not None else "NX-UNKNOWN"


def nx_error_detail(ex: NXOpen.NXException) -> str:
    """`NX <code>: <message>`, the form the C# tools logged and showed."""
    code = getattr(ex, "ErrorCode", "?")
    return f"NX {code}: {_message(ex)}"


def _message(ex: NXOpen.NXException) -> str:
    get_message = getattr(ex, "GetMessage", None)
    return str(get_message()) if callable(get_message) else str(ex)
