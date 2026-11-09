"""BANxOpen Foundation: the Block UI kit. Generic UI mechanics shared by every tool; no business logic.

`Messenger`, `run_with_confirmation` and the tree and menu values (`TreeRow`, `MenuItem`) are pure and imported
directly. The NX-backed names are resolved lazily, so
presenter tests can import this package without NX.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

from banxopen.foundation.ui.messenger import Messenger, run_with_confirmation
from banxopen.foundation.ui.tree_rows import CHECKED, SEPARATOR, UNCHECKED, MenuItem, TreeRow

if TYPE_CHECKING:
    from banxopen.foundation.ui.block_reader import BlockReader
    from banxopen.foundation.ui.callbacks import launch_dialog, ui_callback
    from banxopen.foundation.ui.nx_messenger import NxMessenger
    from banxopen.foundation.ui.tree import TreeBinding, TreeUnavailableError, show_menu

__all__ = [
    "CHECKED",
    "SEPARATOR",
    "UNCHECKED",
    "BlockReader",
    "MenuItem",
    "Messenger",
    "NxMessenger",
    "TreeBinding",
    "TreeRow",
    "TreeUnavailableError",
    "launch_dialog",
    "run_with_confirmation",
    "show_menu",
    "ui_callback",
]

_LAZY = {
    "BlockReader": "block_reader",
    "NxMessenger": "nx_messenger",
    "TreeBinding": "tree",
    "TreeUnavailableError": "tree",
    "show_menu": "tree",
    "launch_dialog": "callbacks",
    "ui_callback": "callbacks",
}


def __getattr__(name: str) -> Any:
    module = _LAZY.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(importlib.import_module(f"{__name__}.{module}"), name)
