"""What a tool puts in a Block UI tree or its context menu, as plain values. Pure: presenters build these and tests
read them; `TreeBinding` and `show_menu` write them to NX."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Final

UNCHECKED: Final = 1
"""`TreeRow.state` for NX's built-in unchecked state icon. NX 2412's tree has no checkbox edit control, so a checkbox
is a state icon; 0 is no icon at all, which makes a row look unpickable."""
CHECKED: Final = 2


@dataclass(frozen=True, slots=True)
class TreeRow[T]:
    """One node. `value` is what a click on it resolves to: None for a structural row (a category, say) the user can
    see but not act on. `columns` maps column id to text, for the columns after the node's own text (column 0)."""

    text: str
    value: T | None = None
    columns: Mapping[int, str] = field(default_factory=dict[int, str])
    children: tuple[TreeRow[T], ...] = ()
    state: int | None = None
    """`UNCHECKED` or `CHECKED` for a checkbox row; None leaves the node's state alone."""
    warning: bool = False
    """Drawn in the warning colour."""


@dataclass(frozen=True, slots=True)
class MenuItem:
    """One context-menu entry: the presenter decides the content and what is enabled, `show_menu` builds it."""

    id: int
    text: str
    enabled: bool = True

    @property
    def is_separator(self) -> bool:
        return self.id == SEPARATOR.id


SEPARATOR: Final = MenuItem(-1, "")
