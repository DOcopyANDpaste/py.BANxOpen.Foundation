from collections.abc import Iterable

from banxopen.foundation import FoundationCodes, FoundationText, RequirementDiff

from builders import spec


class CustomText(FoundationText):
    def requirement_name_claimed(self, name: str, identities: Iterable[str]) -> str:
        return f"custom:{name}"


def test_default_words_a_name_conflict_with_the_name_and_every_claimant():
    diff = RequirementDiff.compute([], [spec(key="A-1"), spec(key="A_1")])

    assert len(diff.errors) == 1
    error = diff.errors[0]
    assert error.startswith("Requirement name '")
    assert "D/A-1/A" in error
    assert "D/A_1/A" in error


def test_an_overriding_describer_words_the_errors_it_is_given():
    diff = RequirementDiff.compute([], [spec(key="A-1"), spec(key="A_1")], CustomText())

    assert len(diff.errors) == 1
    assert diff.errors[0].startswith("custom:")


def test_codes_are_distinct():
    values = [v for k, v in vars(FoundationCodes).items() if k.isupper()]

    assert values
    assert len(values) == len(set(values))
