"""Typed reads and writes of Block UI blocks. Subclass per dialog, with the block IDs as constants."""

# NX 2412's Python stubs declare instance methods without `self`, type enum members as int and give collections
# no __iter__; these rules would only report those stub defects here. Everything else is still checked.
# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportReturnType=false
# pyright: reportCallIssue=false, reportGeneralTypeIssues=false

from collections.abc import Sequence
from typing import Any

import NXOpen
import NXOpen.BlockStyler


class BlockReader:
    """All `FindBlock` lookups for one dialog go through a subclass of this, so when the Styler renames a block only
    that subclass's ID constant changes."""

    def __init__(self, dialog: NXOpen.BlockStyler.BlockDialog) -> None:
        self._top = dialog.TopBlock

    def _block(self, block_id: str) -> Any:  # a UIBlock subtype; the stubs type FindBlock as the base class
        return self._top.FindBlock(block_id)

    def selection(self, block_id: str) -> list[NXOpen.TaggedObject]:
        return list(self._block(block_id).GetSelectedObjects())

    def set_selection(self, block_id: str, objects: Sequence[NXOpen.TaggedObject]) -> None:
        self._block(block_id).SetSelectedObjects(list(objects))

    def double(self, block_id: str) -> float:
        return float(self._block(block_id).Value)

    def set_double(self, block_id: str, value: float) -> None:
        self._block(block_id).Value = value

    def string(self, block_id: str) -> str:
        return str(self._block(block_id).Value)

    def set_list_items(self, block_id: str, items: Sequence[str]) -> None:
        self._block(block_id).SetListItems(list(items))

    def selected_list_item(self, block_id: str) -> str | None:
        return self._block(block_id).SelectedItemString or None

    def set_enabled(self, block_id: str, enabled: bool) -> None:
        self._block(block_id).Enable = enabled

    def set_visible(self, block_id: str, visible: bool) -> None:
        self._block(block_id).Show = visible
