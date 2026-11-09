from typing import Any

from banxopen.foundation import FoundationCodes, OperationResult
from banxopen.foundation.ui import run_with_confirmation


class FakeMessenger:
    def __init__(self, answer: bool) -> None:
        self.answer = answer
        self.asked: list[str] = []
        self.shown: list[OperationResult[Any]] = []

    def show_result(self, result: OperationResult[Any], success_message: str | None = None) -> None:
        self.shown.append(result)

    def ask(self, question: str) -> bool:
        self.asked.append(question)
        return self.answer


class FakeOperation:
    def __init__(self, *results: OperationResult[str]) -> None:
        self._results = list(results)
        self.calls: list[bool] = []

    def __call__(self, confirmed: bool) -> OperationResult[str]:
        self.calls.append(confirmed)
        return self._results.pop(0)


def test_runs_once_when_the_library_does_not_ask():
    operation = FakeOperation(OperationResult.success("done"))
    messenger = FakeMessenger(answer=True)

    result = run_with_confirmation(messenger, operation)

    assert result.value == "done"
    assert operation.calls == [False]
    assert messenger.asked == []


def test_asks_the_library_question_and_retries_confirmed_when_accepted():
    operation = FakeOperation(OperationResult.confirm("Overwrite?"), OperationResult.success("done"))
    messenger = FakeMessenger(answer=True)

    result = run_with_confirmation(messenger, operation)

    assert result.ok
    assert operation.calls == [False, True]
    assert messenger.asked == ["Overwrite?"]


def test_declining_cancels_without_a_second_call():
    operation = FakeOperation(OperationResult.confirm("Overwrite?"))

    result = run_with_confirmation(FakeMessenger(answer=False), operation)

    assert not result.ok
    assert result.error_code == FoundationCodes.CANCELLED
    assert operation.calls == [False]
