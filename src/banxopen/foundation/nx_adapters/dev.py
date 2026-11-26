"""Developer loop helpers. No-ops unless BANXOPEN_DEV=1."""

from __future__ import annotations

import importlib
import os
import sys


def purge_banxopen_modules() -> None:
    """Drop our cached modules so the next import reads fresh source, without restarting NX.

    NX keeps one interpreter for the whole session, so edited `.py` files are otherwise never re-read. Only
    `banxopen.*` is purged; NXOpen extension modules must never be reloaded.
    """
    if os.environ.get("BANXOPEN_DEV") != "1":
        return
    for name in [m for m in sys.modules if m == "banxopen" or m.startswith("banxopen.")]:
        del sys.modules[name]
    importlib.invalidate_caches()
