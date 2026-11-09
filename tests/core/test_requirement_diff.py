from dataclasses import replace

from banxopen.foundation import EqualsValueRule, RequirementDiff, SetOfValuesRule

from builders import spec


def test_compute_creates_missing_deletes_unwanted_leaves_equivalent_alone():
    kept = spec(key="kept")
    gone = spec(key="gone")
    added = spec(key="added")

    diff = RequirementDiff.compute([kept, gone], [replace(kept), added])

    assert diff.to_create == (added,)
    assert diff.to_replace == ()
    assert diff.to_delete == (gone,)
    assert diff.errors == ()


def test_compute_replaces_when_anything_nx_would_show_changed():
    existing = spec(rule=EqualsValueRule(0.04, 0.0005))

    for changed in (
        replace(existing, rule=EqualsValueRule(0.05, 0.0005)),
        replace(existing, description=("other",)),
        replace(existing, associated_object_keys=("101",)),
        replace(existing, checked_formula="other"),
    ):
        assert len(RequirementDiff.compute([existing], [changed]).to_replace) == 1


def test_compute_ignores_associated_object_order_and_number_round_trip_noise():
    existing = spec(rule=EqualsValueRule(0.04, 0.0005), objects=["101", "102"])
    wanted = replace(existing, rule=EqualsValueRule(0.04 + 1e-15, 0.0005), associated_object_keys=("102", "101"))

    assert RequirementDiff.compute([existing], [wanted]).is_empty


def test_compute_value_order_matters_because_nx_shows_it_in_that_order():
    existing = spec(rule=SetOfValuesRule(("a", "b")))

    diff = RequirementDiff.compute([existing], [replace(existing, rule=SetOfValuesRule(("b", "a")))])

    assert len(diff.to_replace) == 1


def test_compute_matches_by_identity_so_a_stem_only_on_the_wanted_spec_changes_nothing():
    # Read back from NX, a spec has no stem; the same requirement wanted again has one.
    existing = spec(key="STD|B1")
    wanted = replace(existing, name_stem="BEAD_B1")

    assert RequirementDiff.compute([existing], [wanted]).is_empty


def test_compute_refuses_stems_that_collapse_to_one_name():
    diff = RequirementDiff.compute(
        [],
        [replace(spec(key="STD1|B1"), name_stem="BEAD_B1"), replace(spec(key="STD2|B1"), name_stem="BEAD_B1")],
    )

    assert diff.errors


def test_compute_refuses_keys_that_collapse_to_one_name():
    diff = RequirementDiff.compute([], [spec(key="A-1"), spec(key="A_1")])

    assert diff.errors
    assert diff.is_empty


def test_compute_deletes_extra_copies_of_a_wanted_requirement():
    first = spec(key="dup")
    copy = spec(key="dup", description=["copied by hand"])

    diff = RequirementDiff.compute([first, copy], [replace(first)])

    assert len(diff.to_delete) == 1
    assert diff.to_delete[0] is copy  # identity: the store deletes the NX object behind this exact read
    assert diff.to_replace == ()


def test_compute_deletes_every_copy_of_an_unwanted_requirement():
    first = spec(key="dup")
    copy = spec(key="dup", description=["copied by hand"])

    diff = RequirementDiff.compute([first, copy], [])

    assert len(diff.to_delete) == 2
