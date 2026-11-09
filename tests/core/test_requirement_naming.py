from dataclasses import replace

from banxopen.foundation.core.requirement_naming import (
    check_name,
    description_with_metadata,
    name_from_identity,
    requirement_name,
    split_description,
)

from builders import spec


def test_name_keeps_a_separator_for_punctuation_so_nearly_equal_keys_stay_distinct():
    assert (
        name_from_identity("SHEETMETAL.BEAD", "BA|B1005010-2", "GRADE") == "BA_REQ_SHEETMETAL_BEAD_BA_B1005010_2_GRADE"
    )
    assert name_from_identity("SHEETMETAL.BEAD", "BA|B1005010-2", "GRADE") != name_from_identity(
        "SHEETMETAL.BEAD", "BA|B10050102", "GRADE"
    )


def test_name_is_upper_cased_and_ascii_only():
    # Space, 'é' and space each become one '_'.
    assert name_from_identity("d", "k é x", "a") == "BA_REQ_D_K___X_A"


def test_name_counts_a_character_outside_the_bmp_as_two_units_like_csharp():
    assert name_from_identity("d", "k\U0001f600", "a") == "BA_REQ_D_K___A"


def test_metadata_round_trips_any_key():
    original = spec(
        domain="SHEETMETAL.BEAD",
        key="Std A|SPEC=1 2%",
        aspect="THICKNESS",
        description=["Bead SPEC 1", "Users: x"],
    )

    description, identity = split_description(description_with_metadata(original))

    assert description == original.description
    assert identity == ("SHEETMETAL.BEAD", "Std A|SPEC=1 2%", "THICKNESS")


def test_metadata_escapes_like_uri_escape_data_string():
    written = description_with_metadata(spec(domain="a/b", key="x~y z", aspect="Q"))[-1]

    assert written == "#BA_REQ v1 domain=a%2Fb key=x~y%20z aspect=Q"


def test_split_description_without_metadata_has_no_identity():
    description, identity = split_description(["written by hand"])

    assert identity is None
    assert description == ("written by hand",)


def test_name_uses_the_name_stem_in_place_of_domain_and_key():
    stemmed = replace(
        spec(domain="SHEETMETAL.BEAD", key="BOMBARDIER B-STANDARDS|B1005010-3", aspect="GRADE"),
        name_stem="BEAD_B1005010-3",
    )

    assert requirement_name(stemmed) == "BA_REQ_BEAD_B1005010_3_GRADE"


def test_name_without_a_stem_is_built_from_the_identity():
    assert requirement_name(spec()) == "BA_REQ_D_K_A"


def test_check_name_derives_from_the_requirement_name():
    assert check_name("BA_REQ_X_Y_Z") == "BA_REQ_X_Y_Z_CHK"
