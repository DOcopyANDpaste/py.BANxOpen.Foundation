"""Pins Foundation's public API. A failure here means the API changed: update the pin deliberately, bump the version
and add a CHANGELOG entry, then run every downstream repo's tests."""

import importlib
import inspect

import banxopen.foundation as api
import banxopen.foundation.nx as nx
import banxopen.foundation.ui as ui


def test_pure_api_names_are_pinned():
    assert set(api.__all__) == {
        "BodyId",
        "BodyInfo",
        "BodyKind",
        "EqualsValueRule",
        "FoundationCodes",
        "FoundationText",
        "GateRule",
        "OperationResult",
        "PartRequirementStore",
        "RequirementDiff",
        "RequirementRead",
        "RequirementRule",
        "RequirementSeverity",
        "RequirementSpec",
        "RequirementStatus",
        "RequirementValueType",
        "RuleDecision",
        "RuleOutcome",
        "SetOfValuesRule",
        "StoredRequirement",
        "__version__",
    }


def test_nx_api_names_are_pinned():
    assert set(nx.__all__) == {
        "BodyResolver",
        "LogSettings",
        "LogTarget",
        "NxDialogText",
        "NxLogHandler",
        "NxSessionContext",
        "UndoScope",
        "create_requirement_store",
        "expression_unlocked",
        "install_batch_logging",
        "install_nx_logging",
        "lock_expression",
        "nx_error_code",
        "nx_error_detail",
    }


def test_ui_kit_names_are_pinned():
    assert set(ui.__all__) == {
        "CHECKED",
        "SEPARATOR",
        "UNCHECKED",
        "BlockReader",
        "MenuItem",
        "Messenger",
        "NxMessenger",
        "TreeBinding",
        "TreeRow",
        "TreeUnavailableError",
        "launch_dialog",
        "run_with_confirmation",
        "show_menu",
        "ui_callback",
    }


def test_every_pure_name_resolves_without_nx():
    for name in api.__all__:
        assert getattr(api, name) is not None


def test_public_packages_import_without_nx():
    for module in (
        "banxopen.foundation",
        "banxopen.foundation.nx",
        "banxopen.foundation.nx.dev",
        "banxopen.foundation.ui",
    ):
        importlib.import_module(module)


def test_requirement_store_protocol_is_pinned():
    store = api.PartRequirementStore
    assert list(inspect.signature(store.read).parameters) == ["self", "domain"]
    assert list(inspect.signature(store.refresh).parameters) == ["self", "domain", "current"]
    assert list(inspect.signature(store.audit).parameters) == ["self", "domain"]


def test_operation_result_fields_are_pinned():
    assert list(api.OperationResult.__dataclass_fields__) == [
        "ok",
        "value",
        "error_code",
        "message",
        "needs_confirmation",
        "question",
    ]
