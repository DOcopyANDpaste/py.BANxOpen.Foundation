# BANxOpen.Foundation (Python)

The shared base every BANxOpen NX tool builds on: result and rule shapes, body identity, part requirements, NX session plumbing, and the Block UI kit. It is the Python port of the C# `BANxOpen.Foundation` for NX 2606 (Designcenter), whose embedded Python is CPython 3.15. Domain-neutral: no materials or sheet metal.

## Public API

Import only from these three packages; everything below them is implementation. The tests in `tests/api/` pin all three.

| Package | Contents | Needs NX? |
|---|---|---|
| `banxopen.foundation` | `OperationResult[T]`, `BodyId`/`BodyInfo`/`BodyKind`, `GateRule`/`RuleOutcome`/`RuleDecision`, requirement specs, `PartRequirementStore`, `RequirementDiff`, `FoundationCodes`, `FoundationText` | no |
| `banxopen.foundation.nx` | `NxSessionContext`, `UndoScope`, `BodyResolver`, `create_requirement_store`, `expression_unlocked`/`lock_expression`, `NxDialogText`, `install_nx_logging`/`install_batch_logging`, `nx_error_code`/`nx_error_detail`; `nx.dev.purge_banxopen_modules` | to use, not to import |
| `banxopen.foundation.ui` | `Messenger`, `run_with_confirmation` (pure); `NxMessenger`, `ui_callback`, `launch_dialog`, `BlockReader` | for the NX-backed names |

```python
from banxopen.foundation import OperationResult
from banxopen.foundation.nx import NxSessionContext, UndoScope, install_nx_logging

install_nx_logging(session)  # entry points only
started = NxSessionContext.try_initialize()
if not started.ok:
    ...  # show started.message
ctx = started.value
with UndoScope(ctx.session, "Apply Material Assignment") as undo:
    ...
    undo.commit()
```

Logging uses the C# environment variables: `BANXOPEN_LOG_TARGET` = `NxLog` | `ListingWindow` | `Both`, and `BANXOPEN_DEBUG` = `1` | `true` | `on`.

## Development

```powershell
python -m venv .venv                       # with Python 3.15: the version NX 2606 embeds (the template's .venv works)
.venv\Scripts\python -m pip install -e ".[dev]"
New-Item -ItemType Junction -Path .\typings -Target "$env:UGII_BASE_DIR\UGOPEN\pythonStubs"   # NXOpen stubs for pyright/Pylance

.venv\Scripts\ruff check . ; .venv\Scripts\ruff format --check .
.venv\Scripts\pyright                       # strict on model/ and core/
.venv\Scripts\lint-imports                  # layers; no NXOpen in core/model
.venv\Scripts\python -m pytest --cov        # runs without NX
```

NX's Python stubs have defects (found in NX 2412's; recheck them against NX 2606's): instance methods declared without `self`, enum members typed as `int`, and collections without `__iter__`. Each NX-touching module turns off only the pyright rules those defects trip, with a comment at the top of the file.

## In NX

1. Run `scripts/smoke_foundation.py` via Alt+F8 on a part with bodies and C#-written `BA_REQ` requirements. It is read-only and reports to the Listing Window.
2. For deployment, `src/banxopen/foundation` is copied to `<root>\lib\banxopen\foundation`. That root is on `UGII_PYTHONPATH` (see the `nxopen-python-library` skill, runtime-and-deployment).
