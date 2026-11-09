from banxopen.foundation import OperationResult, RuleDecision, RuleOutcome


def test_success_is_ok_with_no_error_code_or_message():
    result = OperationResult.success()

    assert result.ok
    assert result.error_code is None
    assert result.message is None


def test_fail_is_not_ok_and_carries_code_and_message():
    result = OperationResult.fail("E001", "Something went wrong.")

    assert not result.ok
    assert result.error_code == "E001"
    assert result.message == "Something went wrong."


def test_success_carries_a_value_and_an_optional_message():
    result = OperationResult.success(42, message="Done.")

    assert result.ok
    assert result.value == 42
    assert result.message == "Done."


def test_fail_leaves_the_value_empty():
    result: OperationResult[int] = OperationResult.fail("E001", "No.")

    assert result.value is None


def test_confirm_asks_a_question_and_is_not_ok():
    result = OperationResult.confirm("Overwrite?")

    assert not result.ok
    assert result.needs_confirmation
    assert result.question == "Overwrite?"
    assert result.error_code is None


def test_rule_outcome_defaults_to_no_args_and_no_inner_outcomes():
    outcome = RuleOutcome("R1", RuleDecision.ALLOW, None, None)

    assert dict(outcome.args) == {}
    assert outcome.inner == ()
