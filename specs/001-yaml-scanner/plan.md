# Implementation Plan: YAML File Scanner

**Branch**: `001-yaml-scanner` | **Date**: 2026-01-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-yaml-scanner/spec.md`

## Summary

Implement the first stage of the ArgoCD Application migrator pipeline: a CLI-based YAML file scanner that discovers `.yaml` and `.yml` files in specified directories. The scanner supports both single-directory and recursive scanning modes, provides multiple output formats (JSON and human-readable), configurable verbosity levels, and follows Unix conventions for stdout/stderr/exit codes. This scanner serves as the entry point for the 4-stage migration pipeline (Scanner → Parser → Migrator → Validator).

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: Typer (CLI framework), Rich (terminal output), pathlib (file operations)
**Storage**: N/A (file system scanning only, no persistence)
**Testing**: pytest (unit, integration, contract tests)
**Target Platform**: macOS, Linux, Windows (cross-platform CLI)
**Project Type**: Single CLI application
**Performance Goals**: Scan 10,000 files in under 5 seconds; CLI help/validation responds within 500ms
**Constraints**: Memory usage <512MB; no symlink following in recursive mode to prevent cycles
**Scale/Scope**: Handle directory trees with 100,000+ files; support deeply nested structures (10+ levels)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. CLI-First Design ✅

- All functionality accessible via CLI with Typer framework
- Input via `--input-dir` argument
- Output to stdout (results) and stderr (errors)
- Support both JSON (`--format json`) and human-readable output
- Exit codes: 0 for success, 1 for errors

### II. Test Coverage Required ✅

- Unit tests for scanner logic, path resolution, filtering
- Integration tests for directory traversal scenarios
- Contract tests not applicable (no external APIs)
- Will use pytest with coverage measurement
- Tests will run in CI before merge

### III. Type Safety ✅

- Python 3.12+ with type annotations on all functions
- Use TypedDict or Pydantic for ScanResult and ScanOptions
- Type checking with pyright or mypy in strict mode
- No `Any` types without justification

### IV. Security-First ✅

- Path traversal prevention: validate input directory path
- No secrets/credentials involved in file scanning
- Permission errors handled gracefully without crashes
- Input validation for all CLI parameters

### V. Simplicity and Performance ✅

- Simple file scanning with pathlib - no complex frameworks
- Streaming approach (yield files as found, not load all into memory)
- Memory bounded by design (no large data structures)
- No premature optimization; straightforward implementation
- Progress reporting not required for scanner stage (deferred to later pipeline stages if needed)

### Pipeline Architecture ✅

- Scanner is Stage 1 of 4 (Scanner → Parser → Migrator → Validator)
- Clear input: directory path + options
- Clear output: JSON array of file paths to stdout
- Independently testable via pytest
- Errors in processing do not halt (continue scanning accessible paths)

**Gate Status**: PASSED ✅ - All constitution principles satisfied

## Project Structure

### Documentation (this feature)

```text
specs/001-yaml-scanner/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: Technology research
├── data-model.md        # Phase 1: Data structures
├── quickstart.md        # Phase 1: User guide
└── contracts/           # Phase 1: CLI interface contracts
```

### Source Code (repository root)

```text
src/
├── scanner/
│   ├── __init__.py
│   ├── core.py          # ScanResult, ScanOptions, scanner logic
│   ├── filters.py       # Hidden dir filtering, extension matching
│   └── cli.py           # Typer CLI application
└── __init__.py

tests/
├── unit/
│   ├── test_scanner_core.py
│   ├── test_filters.py
│   └── test_cli_parsing.py
├── integration/
│   ├── test_single_directory_scan.py
│   ├── test_recursive_scan.py
│   └── test_permission_errors.py
└── fixtures/
    └── sample_directories/  # Test directory structures

pyproject.toml           # UV project configuration
README.md                # User-facing documentation
.python-version          # Python 3.12
```

**Structure Decision**: Single project structure chosen because this is a standalone CLI tool with no frontend/backend separation or multiple services. All code resides in `src/scanner/` with tests in `tests/`. Using Python package structure for clean imports and future extensibility to Parser/Migrator/Validator stages.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - No constitution violations. Implementation follows all principles without requiring exceptions.
