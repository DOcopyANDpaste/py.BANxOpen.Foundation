"""BANxOpen Foundation: NX API.

Importable without NX: every name is resolved lazily on first use, so tests and type checkers can import this module.
Using the names (other than the logging settings) needs a running NX session.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from banxopen.foundation.core.requirement_store import PartRequirementStore
    from banxopen.foundation.nx_adapters.body_resolver import BodyResolver
    from banxopen.foundation.nx_adapters.dialog_text import NxDialogText
    from banxopen.foundation.nx_adapters.errors import nx_error_code, nx_error_detail
    from banxopen.foundation.nx_adapters.expression_lock import expression_unlocked, lock_expression
    from banxopen.foundation.nx_adapters.nx_logging import (
        LogSettings,
        LogTarget,
        NxLogHandler,
        install_batch_logging,
        install_nx_logging,
    )
    from banxopen.foundation.nx_adapters.session_context import NxSessionContext
    from banxopen.foundation.nx_adapters.undo_scope import UndoScope
    from banxopen.foundation.text import FoundationText

__all__ = [
    "BodyResolver",
    "LogSettings",
    "LogTarget",
    "NxDialogText",
    "NxLogHandler",
    "NxSessionContext",
    "UndoScope",
    "create_requirement_store",
    "expression_unlocked",
    "install_batch_logging",
    "install_nx_logging",
    "lock_expression",
    "nx_error_code",
    "nx_error_detail",
]

_ADAPTERS = "banxopen.foundation.nx_adapters"
_LAZY = {
    "BodyResolver": "body_resolver",
    "LogSettings": "nx_logging",
    "LogTarget": "nx_logging",
    "NxDialogText": "dialog_text",
    "NxLogHandler": "nx_logging",
    "NxSessionContext": "session_context",
    "UndoScope": "undo_scope",
    "expression_unlocked": "expression_lock",
    "install_batch_logging": "nx_logging",
    "install_nx_logging": "nx_logging",
    "lock_expression": "expression_lock",
    "nx_error_code": "errors",
    "nx_error_detail": "errors",
}


def __getattr__(name: str) -> Any:
    module = _LAZY.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(importlib.import_module(f"{_ADAPTERS}.{module}"), name)


def create_requirement_store(context: NxSessionContext, text: FoundationText | None = None) -> PartRequirementStore:
    """The part requirement store for the context's work part. Run `refresh` inside your own `UndoScope`."""
    from banxopen.foundation.nx_adapters.requirement_store import NxPartRequirementStore

    return NxPartRequirementStore(context, text)
