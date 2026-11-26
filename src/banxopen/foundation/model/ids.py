"""Identifiers Core-layer code can hold without NXOpen."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BodyId:
    """One body within a part.

    The value is the live NX Body's journal identifier: the one handle that is stable across a save/reopen and that
    Core-layer code can hold. Shared by every tool that reads or writes body state, so a body means the same thing to
    every tool and to a feature domain describing what sits on it.
    """

    value: str

    def __str__(self) -> str:
        return self.value
