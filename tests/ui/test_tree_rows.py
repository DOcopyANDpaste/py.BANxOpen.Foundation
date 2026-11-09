from banxopen.foundation.ui import SEPARATOR, MenuItem, TreeRow


def test_a_separator_is_recognised_by_id():
    assert SEPARATOR.is_separator
    assert not MenuItem(1, "Refresh").is_separator


def test_a_tree_row_defaults_to_a_plain_structural_node():
    row: TreeRow[str] = TreeRow("Steels")
    assert row.value is None
    assert dict(row.columns) == {}
    assert row.children == ()
    assert row.state is None
    assert not row.warning
