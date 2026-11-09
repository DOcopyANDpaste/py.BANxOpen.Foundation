"""Holds `RequirementSpec`s in the work part as native NX Requirements.

Each requirement is linked to its checked expression by a Requirement Check (`Requirement.NewCheck`). NX re-evaluates
the checks on every change (`Validation.UpdateTime.EveryChange`), so a requirement keeps watching the part after the
tool that wrote it has closed, and with no BANxOpen code loaded at all.

A changed requirement is replaced (its check and itself deleted, then both created again) rather than edited through
`CreateRequirementBuilder(existing)`: deleting and creating are the two operations whose undo behaviour inside the
caller's undo mark is known, and a requirement holds nothing worth preserving across a change.

API checked against the NX 2412 Python stubs (`NXOpen.Validate`).
"""

# NX 2412's Python stubs declare instance methods without `self`, type enum members as int and give collections
# no __iter__; these rules would only report those stub defects here. Everything else is still checked.
# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportReturnType=false
# pyright: reportCallIssue=false, reportGeneralTypeIssues=false

import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import NXOpen
import NXOpen.Validate

from banxopen.foundation.codes import FoundationCodes
from banxopen.foundation.core.requirement_diff import RequirementDiff
from banxopen.foundation.core.requirement_naming import (
    check_name,
    description_with_metadata,
    requirement_name,
    split_description,
)
from banxopen.foundation.model.requirements import (
    EqualsValueRule,
    RequirementRead,
    RequirementRule,
    RequirementSeverity,
    RequirementSpec,
    RequirementStatus,
    RequirementValueType,
    SetOfValuesRule,
    StoredRequirement,
)
from banxopen.foundation.model.results import OperationResult
from banxopen.foundation.nx_adapters.dialog_text import NxDialogText
from banxopen.foundation.nx_adapters.errors import nx_error_detail
from banxopen.foundation.nx_adapters.session_context import NxSessionContext
from banxopen.foundation.text import FoundationText

_log = logging.getLogger(__name__)

_Builder = NXOpen.Validate.RequirementBuilder


@dataclass(frozen=True, slots=True, eq=False)
class _Owned:
    spec: RequirementSpec
    status: RequirementStatus
    requirement: NXOpen.Validate.Requirement
    check: NXOpen.Validate.RequirementCheck | None
    nx_name: str


class NxPartRequirementStore:
    """Implements `PartRequirementStore`. Create it through `banxopen.foundation.nx.create_requirement_store`."""

    def __init__(self, context: NxSessionContext, text: FoundationText | None = None) -> None:
        self._context = context
        self._text = text or FoundationText.DEFAULT

    @property
    def _work_part(self) -> NXOpen.Part:
        return self._context.work_part

    # ---- PartRequirementStore ----

    def read(self, domain: str) -> RequirementRead:
        owned, errors = self._read_owned(domain)
        return RequirementRead(tuple(StoredRequirement(o.spec, o.status) for o in owned), tuple(errors))

    def refresh(self, domain: str, current: Sequence[RequirementSpec]) -> OperationResult[None]:
        foreign = [requirement_name(s) for s in current if s.domain != domain]
        if foreign:
            return OperationResult.fail(
                FoundationCodes.REQUIREMENT_WRONG_DOMAIN, self._text.requirements_wrong_domain(foreign, domain)
            )

        owned, read_errors = self._read_owned(domain)
        if read_errors:
            # Never write over what could not be read: an unreadable requirement would look absent and be
            # duplicated, or look unwanted and be deleted without anyone knowing what it said.
            return OperationResult.fail(
                FoundationCodes.REQUIREMENTS_UNREADABLE, self._text.requirements_unreadable(read_errors)
            )

        diff = RequirementDiff.compute([o.spec for o in owned], current, self._text)
        if diff.errors:
            return OperationResult.fail(
                FoundationCodes.REQUIREMENT_NAME_CONFLICT, self._text.requirement_name_conflict(diff.errors)
            )

        renamed = 0
        try:
            for spec in (*diff.to_delete, *(existing for existing, _ in diff.to_replace)):
                self._delete(next(o for o in owned if o.spec is spec))

            written = (*diff.to_create, *(wanted for _, wanted in diff.to_replace))
            for spec in written:
                self._create(spec)

            # Unchanged ones still take the current naming (a part written before name_stem existed, say).
            # Ownership is the description's identity line, so renaming loses nothing.
            written_ids = {id(s) for s in written}
            for spec in current:
                if id(spec) in written_ids:
                    continue
                kept = next((o for o in owned if _same_identity(o.spec, spec)), None)
                if kept is not None and self._rename(kept, requirement_name(spec)):
                    renamed += 1
        except NXOpen.NXException as ex:
            _log.error("Writing requirements for '%s' failed: %s", domain, nx_error_detail(ex))
            return OperationResult.fail(
                FoundationCodes.REQUIREMENT_WRITE_FAILED,
                self._text.requirement_write_failed(NxDialogText.DEFAULT.nx_error(ex)),
            )

        if not diff.is_empty or renamed:
            _log.debug(
                "Requirements for '%s': %d created, %d replaced, %d deleted, %d renamed.",
                domain,
                len(diff.to_create),
                len(diff.to_replace),
                len(diff.to_delete),
                renamed,
            )

        self._evaluate(domain)
        return OperationResult.success()

    def audit(self, domain: str) -> list[str]:
        """One line per requirement `domain` owns: its tag, its check's, and every object the check is associated
        with, each as alive or not. A dead tag held by a check is what NX refuses on save ("an invalid tag was passed
        to the tag module")."""
        owned, errors = self._read_owned(domain)
        lines = [f"read error: {e}" for e in errors]
        for o in owned:
            line = f"{o.nx_name} [{self._tag_status(o.requirement.Tag)}]"
            check = o.check
            if check is None:
                lines.append(f"{line}, no check")
                continue

            line += f", check [{self._tag_status(check.Tag)}] result {_safe_result(check)}"
            try:
                objects = check.GetAssociatedObjects() or []
                described = ["null" if obj is None else f"{obj.Tag} {self._tag_status(obj.Tag)}" for obj in objects]
                line += f", associated [{', '.join(described)}]"
            except NXOpen.NXException as ex:
                line += f", associated objects unreadable: {nx_error_detail(ex)}"
            lines.append(line)
        return lines

    # ---- Evaluating ----

    def _evaluate(self, domain: str) -> None:
        """Evaluates every check `domain` owns. A check NX has never evaluated reports Unknown until something it
        watches changes, and a check on an expression outside the update graph may never see a change. One that
        fails to evaluate is logged; the rest still run."""
        owned, _ = self._read_owned(domain)
        for o in owned:
            if o.check is None:
                continue
            try:
                o.check.Evaluate()
                _log.debug("Requirement check '%s' evaluated: %s.", o.nx_name, _safe_result(o.check))
            except NXOpen.NXException as ex:
                _log.warning("Requirement check '%s' could not be evaluated: %s", o.nx_name, nx_error_detail(ex))

    def _tag_status(self, tag: int) -> str:
        return "alive" if self._context.is_alive(tag) else "DEAD"

    # ---- Reading ----

    def _read_owned(self, domain: str) -> tuple[list[_Owned], list[str]]:
        owned: list[_Owned] = []
        errors: list[str] = []
        try:
            requirements = list(self._work_part.Requirements)
            checks = list(self._work_part.RequirementChecks)
        except NXOpen.NXException as ex:
            errors.append(self._text.requirements_not_listed(NxDialogText.DEFAULT.nx_error(ex)))
            return owned, errors

        # Every requirement is opened, not only those named BA_REQ_*: ownership is decided by the bookkeeping line in
        # the description, so a requirement whose NX name did not come out as written is still found, never duplicated.
        for requirement in requirements:
            name = _safe_name(requirement)
            try:
                check = next((c for c in checks if _parent_tag(c) == requirement.Tag), None)
                read = self._read_spec(requirement, check)
                if read is not None and read.spec.domain == domain:
                    owned.append(read)
            except NXOpen.NXException as ex:
                errors.append(self._text.requirement_unreadable(name, NxDialogText.DEFAULT.nx_error(ex)))
            except ValueError as ex:
                errors.append(self._text.requirement_value_unreadable(name, str(ex)))
        return owned, errors

    def _read_spec(
        self, requirement: NXOpen.Validate.Requirement, check: NXOpen.Validate.RequirementCheck | None
    ) -> _Owned | None:
        """None for a requirement carrying no BANxOpen identity line: not ours to read or to touch."""
        builder = self._work_part.Requirements.CreateRequirementBuilder(requirement)
        try:
            description, identity = split_description(builder.GetRequirementDescription() or [])
            if identity is None:
                return None

            rule: RequirementRule
            if builder.DefinitionMethodOption == _Builder.DefinitionMethodOptions.SetOfValues:
                rule = SetOfValuesRule(tuple(builder.GetValidValues() or []))
            else:
                rule = EqualsValueRule(float(builder.SingleSidedValue), builder.RequirementTolerance)

            domain, key, aspect = identity
            spec = RequirementSpec(
                domain=domain,
                key=key,
                aspect=aspect,
                value_type=(
                    RequirementValueType.STRING
                    if builder.DataTypeOption == _Builder.DataTypeOptions.String
                    else RequirementValueType.NUMBER
                ),
                rule=rule,
                severity=_severity_from_nx(builder.SeverityOption),
                checked_formula=(check.Formula or "") if check is not None else "",
                description=description,
                associated_object_keys=self._associated_keys(check),
            )
            status = RequirementStatus.UNKNOWN if check is None else _status_from_nx(check.GetCheckResult())
            return _Owned(spec, status, requirement, check, _safe_name(requirement))
        finally:
            builder.Destroy()

    def _associated_keys(self, check: NXOpen.Validate.RequirementCheck | None) -> tuple[str, ...]:
        """The check's associated objects that are still alive. A deleted feature the check still holds is left out,
        so the read no longer matches what is wanted and the next refresh rewrites the check without it."""
        if check is None:
            return ()
        everything = list(check.GetAssociatedObjects() or [])
        alive = [o for o in everything if o is not None and self._context.is_alive(o.Tag)]
        if len(alive) != len(everything):
            _log.warning(
                "Requirement check '%s' holds %d deleted object(s); its next refresh drops them.",
                _safe_check_name(check),
                len(everything) - len(alive),
            )
        return tuple(str(o.Tag) for o in alive)

    # ---- Writing ----

    def _delete(self, owned: _Owned) -> None:
        if owned.check is not None:
            owned.check.Delete()
        owned.requirement.Delete()

    def _rename(self, owned: _Owned, name: str) -> bool:
        """Gives a kept requirement, and its check, `name`. False when it already has it."""
        if owned.nx_name == name:
            return False
        owned.requirement.SetName(name)
        if owned.check is not None:
            owned.check.CheckName = check_name(name)
        _log.debug("Requirement '%s' renamed to '%s'.", owned.nx_name, name)
        return True

    def _create(self, spec: RequirementSpec) -> None:
        name = requirement_name(spec)
        builder = self._work_part.Requirements.CreateRequirementBuilder(None)
        try:
            builder.RequirementTypeOption = _Builder.RequirementTypeOptions.ValidationLimit
            builder.Name = name
            builder.DataTypeOption = (
                _Builder.DataTypeOptions.String
                if spec.value_type is RequirementValueType.STRING
                else _Builder.DataTypeOptions.Number
            )
            builder.SeverityOption = _severity_to_nx(spec.severity)

            match spec.rule:
                case SetOfValuesRule(values=values):
                    builder.DefinitionMethodOption = _Builder.DefinitionMethodOptions.SetOfValues
                    builder.SetValidValues(list(values))
                case EqualsValueRule(value=value, tolerance=tolerance):
                    builder.DefinitionMethodOption = _Builder.DefinitionMethodOptions.SingleSidedComparison
                    builder.RelationalOperatorOption = _Builder.RelationalOperatorOptions.Equal
                    builder.SingleSidedValue = repr(value)  # shortest round-trip form, like C# "R"
                    builder.RequirementTolerance = tolerance

            builder.SetRequirementDescription(list(description_with_metadata(spec)))
            requirement = builder.Commit()
        finally:
            builder.Destroy()

        check = requirement.NewCheck(check_name(name), spec.checked_formula)
        check.SetUpdateControl(NXOpen.Validation.UpdateTime.EveryChange)

        objects = self._resolve_objects(spec.associated_object_keys, name)
        if objects:
            check.SetAssociatedObjects(objects)

    def _resolve_objects(self, keys: Iterable[str], requirement_name: str) -> list[NXOpen.NXObject]:
        """A key that no longer resolves (the feature was deleted since the inventory was read) is left out with a
        warning: the check still guards the part, it just highlights one object fewer."""
        objects: list[NXOpen.NXObject] = []
        for key in keys:
            found: NXOpen.NXObject | None = None
            try:
                # Alive first: a tag of a deleted object can still come back from the manager, and handing it to the
                # check leaves a dead reference in the part that fails its save.
                tag = int(key)
                if self._context.is_alive(tag):
                    obj = NXOpen.TaggedObjectManager.GetTaggedObject(tag)
                    found = obj if isinstance(obj, NXOpen.NXObject) else None
            except ValueError, NXOpen.NXException:
                found = None

            if found is None:
                _log.warning(
                    "Requirement '%s': object %s no longer exists and is not highlighted by its check.",
                    requirement_name,
                    key,
                )
            else:
                objects.append(found)
        return objects


def _same_identity(a: RequirementSpec, b: RequirementSpec) -> bool:
    return (a.domain, a.key, a.aspect) == (b.domain, b.key, b.aspect)


def _parent_tag(check: NXOpen.Validate.RequirementCheck) -> int | None:
    parent = check.ParentRequirement
    return parent.Tag if parent is not None else None


def _safe_name(requirement: NXOpen.Validate.Requirement) -> str:
    try:
        return requirement.Name
    except NXOpen.NXException:
        return f"(tag {requirement.Tag})"


def _safe_check_name(check: NXOpen.Validate.RequirementCheck) -> str:
    try:
        return check.CheckName
    except NXOpen.NXException:
        return f"(tag {check.Tag})"


def _safe_result(check: NXOpen.Validate.RequirementCheck) -> str:
    try:
        return _status_from_nx(check.GetCheckResult()).value
    except NXOpen.NXException as ex:
        return f"unreadable (NX {getattr(ex, 'ErrorCode', '?')})"


def _severity_to_nx(severity: RequirementSeverity) -> _Builder.SeverityOptions:
    if severity is RequirementSeverity.ERROR:
        return _Builder.SeverityOptions.Error
    if severity is RequirementSeverity.INFORMATION:
        return _Builder.SeverityOptions.Information
    return _Builder.SeverityOptions.Warning


def _severity_from_nx(severity: _Builder.SeverityOptions) -> RequirementSeverity:
    if severity == _Builder.SeverityOptions.Error:
        return RequirementSeverity.ERROR
    if severity == _Builder.SeverityOptions.Information:
        return RequirementSeverity.INFORMATION
    return RequirementSeverity.WARNING


def _status_from_nx(result: NXOpen.Validation.Result) -> RequirementStatus:
    results = NXOpen.Validation.Result
    mapping = {
        results.Pass: RequirementStatus.PASS,
        results.Information: RequirementStatus.INFORMATION,
        results.Warning: RequirementStatus.WARNING,
        results.Failed: RequirementStatus.FAILED,
        results.Skipped: RequirementStatus.SKIPPED,
    }
    return mapping.get(result, RequirementStatus.UNKNOWN)
