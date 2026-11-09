"""Behaviour the C# code had but its tests did not pin; pinned here so the port stays faithful."""

from dataclasses import replace

import pytest

from banxopen.foundation import (
    BodyId,
    EqualsValueRule,
    FoundationText,
    RequirementDiff,
    RequirementRead,
    SetOfValuesRule,
)
from banxopen.foundation.core.requirement_naming import split_description

from builders import spec


def test_body_id_prints_as_its_value():
    assert str(BodyId("HANDLE R-123")) == "HANDLE R-123"


def test_requirement_read_is_ok_only_without_errors():
    assert RequirementRead((), ()).ok
    assert not RequirementRead((), ("unreadable",)).ok


def test_a_set_rule_never_equals_an_equals_rule():
    existing = spec(rule=SetOfValuesRule(("1",)))

    diff = RequirementDiff.compute([existing], [replace(existing, rule=EqualsValueRule(1.0, 0.0))])

    assert len(diff.to_replace) == 1


def test_metadata_ignores_fields_without_a_value_separator():
    _, identity = split_description(["#BA_REQ v1 junk domain=D key=K aspect=A"])

    assert identity == ("D", "K", "A")


def test_metadata_missing_a_field_is_not_an_identity():
    description, identity = split_description(["#BA_REQ v1 domain=D key=K"])

    assert identity is None
    assert description == ("#BA_REQ v1 domain=D key=K",)


def test_metadata_repeating_a_field_is_reported_not_guessed():
    # C# ToDictionary threw on a repeated key; the store reports a ValueError as an unreadable requirement.
    with pytest.raises(ValueError, match="repeats the field 'key'"):
        split_description(["#BA_REQ v1 domain=D key=K key=L aspect=A"])


def test_only_the_first_metadata_line_is_the_identity():
    description, identity = split_description(
        ["#BA_REQ v1 domain=D key=K aspect=A", "#BA_REQ v1 domain=X key=Y aspect=Z"]
    )

    assert identity == ("D", "K", "A")
    assert description == ("#BA_REQ v1 domain=X key=Y aspect=Z",)


def test_foundation_text_matches_the_csharp_wording():
    text = FoundationText.DEFAULT

    assert text.no_active_session == "No active NX session."
    assert text.no_work_part == "No active work part. Open a part before launching this tool."
    assert text.requirements_wrong_domain(["N1", "N2"], "D") == "Requirements N1, N2 do not belong to domain 'D'."
    assert text.requirements_unreadable(["a.", "b."]) == "a. b."
    assert text.requirement_name_conflict(["a.", "b."]) == "a. b."
    assert text.requirement_write_failed("NX 1: x") == "NX 1: x"
    assert text.requirements_not_listed("NX 1: x") == "The part's requirements could not be listed: NX 1: x"
    assert text.requirement_unreadable("R", "NX 1: x") == "Requirement 'R' could not be read: NX 1: x"
    assert text.requirement_value_unreadable("R", "bad") == "Requirement 'R' holds a value that could not be read: bad"
    assert text.requirement_name_claimed("R", ["D/K/A", "D/L/A"]) == "Requirement name 'R' is claimed by D/K/A, D/L/A."
