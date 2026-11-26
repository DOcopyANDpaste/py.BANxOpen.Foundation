"""Bodies as read off the live model into a form Core-layer code can hold."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from banxopen.foundation.model.ids import BodyId


class BodyKind(Enum):
    SOLID = "Solid"
    SHEET = "Sheet"
    """A zero-thickness surface body (NX `Body.IsSheetBody`). Not sheet metal."""
    SHEET_METAL = "SheetMetal"
    """A sheet metal body. Solid in NX (`IsSheetBody` is false), recognised through the sheet metal manager. Kept
    distinct because sheet metal material libraries apply to these bodies only."""
    UNKNOWN = "Unknown"


@dataclass(frozen=True, slots=True)
class BodyInfo:
    """One body in a part. `attributes` carries the body's NX user attributes verbatim (title to string value), which
    is how feature domains recognise their own stamps without the reader knowing about them."""

    id: BodyId
    name: str
    kind: BodyKind
    volume: float
    attributes: Mapping[str, str]
