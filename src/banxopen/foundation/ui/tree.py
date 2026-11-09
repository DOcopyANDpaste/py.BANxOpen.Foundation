"""A Block UI tree's contents and the mapping from its nodes back to the values they were rendered from."""

# NX 2412's Python stubs declare instance methods without `self`, type enum members as int and give collections
# no __iter__; these rules would only report those stub defects here. Everything else is still checked.
# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportReturnType=false
# pyright: reportCallIssue=false, reportGeneralTypeIssues=false

import logging
from collections.abc import Callable, Sequence
from typing import Final

import NXOpen
import NXOpen.BlockStyler

from banxopen.foundation.nx_adapters.errors import nx_error_detail
from banxopen.foundation.ui.tree_rows import MenuItem, TreeRow

_log = logging.getLogger(__name__)

WARNING_COLOR: Final = 36
"""A foreground colour from NX's palette, for `TreeRow.warning`."""


class TreeUnavailableError(Exception):
    """NX would not let the tree be rebuilt, typically because its native control does not exist right now (its tab
    page is not built, or NX recreated the dialog's controls). Recoverable: rebuild once the control is back."""


class TreeBinding[T]:
    """Every tree goes through one of these, so the rebuild idiom and the node-to-value lookup exist once. A selection
    is never turned back into a value by parsing what the tree displays: it is mapped through what was last shown.

    Nodes are keyed by `Tag`, not by the node object: NX can hand a callback a fresh wrapper for an existing node."""

    def __init__(self, tree: NXOpen.BlockStyler.Tree) -> None:
        self._tree = tree
        self._by_tag: dict[int, T] = {}
        self._nodes: list[tuple[NXOpen.BlockStyler.Node, T]] = []
        self.is_rebuilding = False
        """True while `show` runs: NX fires select handlers as nodes are deleted, and those must not query a tree that
        is half torn down."""

    def show(self, rows: Sequence[TreeRow[T]], *, expand_roots: bool = True) -> None:
        """Replaces the tree's contents with `rows`, in their order (the tree never re-sorts them), painting once.
        `expand_roots` opens each top-level row one level. Raises `TreeUnavailableError` when NX refuses; the old
        mapping is dropped, so no stale node can resolve."""
        self.is_rebuilding = True
        try:
            self._tree.Redraw(False)
            try:
                self._clear()
                for row in rows:
                    self._add(row, None)
                if expand_roots:
                    self._expand_roots()
            finally:
                self._tree.Redraw(True)
        except NXOpen.NXException as ex:
            self._by_tag.clear()
            self._nodes.clear()
            raise TreeUnavailableError(f"The tree could not be rebuilt: {nx_error_detail(ex)}") from ex
        finally:
            self.is_rebuilding = False

    def resolve(self, node: NXOpen.BlockStyler.Node | None) -> T | None:
        return self._by_tag.get(node.Tag) if node is not None else None

    def resolve_selected(self) -> list[T]:
        if self.is_rebuilding:
            return []
        selected = self._tree.GetSelectedNodes() or []
        return [v for v in (self.resolve(n) for n in selected) if v is not None]

    def resolve_selected_or(self, clicked: NXOpen.BlockStyler.Node | None) -> list[T]:
        """What a context-menu command acts on: the selection when there is one, otherwise the row right-clicked."""
        selected = self.resolve_selected()
        if selected:
            return selected
        single = self.resolve(clicked)
        return [single] if single is not None else []

    def set_states(self, state_of: Callable[[T], int]) -> None:
        """Re-asserts every node's state icon, e.g. to keep a checkbox radio-like after a click (NX does not fire the
        state-change handler for `SetState` calls)."""
        for node, value in self._nodes:
            node.SetState(state_of(value))

    def is_stale(self) -> bool:
        """True when the nodes this holds are no longer the tree's: the tree was emptied behind its back, or a held
        node no longer answers. Seen after a sketch drawn on the fly in the same dialog is cancelled: the rollback can
        take the tree's nodes with it. A stale binding must be shown again, never written through."""
        if not self._nodes:
            return False
        try:
            if self._tree.RootNode is None:
                return True
            _ = self._nodes[0][0].DisplayText
        except Exception:  # noqa: BLE001  (any failure to answer means the node is gone)
            return True
        return False

    def _add(self, row: TreeRow[T], parent: NXOpen.BlockStyler.Node | None) -> None:
        node = self._tree.CreateNode(row.text)
        # AlwaysLast, not Sort: the order was decided before the rows got here.
        self._tree.InsertNode(node, parent, None, NXOpen.BlockStyler.Tree.NodeInsertOption.AlwaysLast)
        for column, text in row.columns.items():
            node.SetColumnDisplayText(column, text)
        if row.state is not None:
            node.SetState(row.state)
        if row.warning:
            node.ForegroundColor = WARNING_COLOR
        if row.value is not None:
            self._by_tag[node.Tag] = row.value
            self._nodes.append((node, row.value))
        for child in row.children:
            self._add(child, node)

    def _expand_roots(self) -> None:
        node = self._tree.RootNode
        while node is not None:
            if node.FirstChildNode is not None:
                node.Expand(NXOpen.BlockStyler.Node.ExpandOption.Expand)
            node = node.NextSiblingNode

    def _clear(self) -> None:
        """Roots first, then delete: deleting a node invalidates it, so the sibling chain cannot be walked while
        deleting from it, and a root takes its subtree with it. A node already gone (see `is_stale`) ends the walk or
        is skipped: the rebuild that follows is the point."""
        roots: list[NXOpen.BlockStyler.Node] = []
        try:
            node = self._tree.RootNode
            while node is not None:
                roots.append(node)
                node = node.NextSiblingNode
        except NXOpen.NXException:
            _log.debug("Tree walk stopped at a node that is gone.")
        for root in roots:
            try:
                self._tree.DeleteNode(root)
            except NXOpen.NXException:
                _log.debug("A tree node was already gone.")
        self._by_tag.clear()
        self._nodes.clear()


def show_menu(tree: NXOpen.BlockStyler.Tree, items: Sequence[MenuItem]) -> None:
    """Builds `items` into the tree's context menu. Call from the tree's menu handler."""
    if not items:
        return
    menu = tree.CreateMenu()
    try:
        for item in items:
            if item.is_separator:
                menu.AddSeparator()
                continue
            menu.AddMenuItem(item.id, item.text)
            if not item.enabled:
                menu.SetItemDisable(item.id, True)
        tree.SetMenu(menu)
    finally:
        menu.Dispose()  # only after SetMenu: the tree takes its copy there
