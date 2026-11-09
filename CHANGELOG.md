# Changelog

All notable changes to the public API (`banxopen.foundation`, `banxopen.foundation.nx`, `banxopen.foundation.ui`). Versioning is semantic, measured on the public API.

## [1.1.0] - 2026-10-28

### Added
- ui-kit trees and menus, shared by the Material Assignment and Bead tools, which each had their own C# `TreeBinding`:
  - pure values: `TreeRow` (text, value, columns, children, checkbox `state`, `warning`), `MenuItem`, `SEPARATOR`,
    `CHECKED` / `UNCHECKED`;
  - NX: `TreeBinding` (`show`, `resolve`, `resolve_selected`, `resolve_selected_or`, `set_states`, `is_stale`),
    `TreeUnavailableError`, `show_menu`.

## [1.0.1] - 2026-10-28

### Fixed
- Ship the PEP 561 `py.typed` marker, so downstream repos (Materials) can type-check against Foundation in pyright strict mode.

## [1.0.0] - 2026-10-28

### Added
- Python port of C# BANxOpen.Foundation for NX 2412 (CPython 3.11).
- `OperationResult[T]` with a confirmation flow (`confirm`, `needs_confirmation`, `question`).
- ui-kit: `Messenger`, `run_with_confirmation`, `NxMessenger`, `ui_callback`, `launch_dialog`, `BlockReader`.
- Logging through the standard `logging` module: `install_nx_logging`, `install_batch_logging`.
- `FoundationCodes`: `NO_ACTIVE_SESSION`, `NO_WORK_PART`, `SESSION_UNAVAILABLE`, `CANCELLED`.
