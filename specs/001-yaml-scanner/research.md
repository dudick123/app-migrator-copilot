# Research: YAML File Scanner

**Feature**: YAML File Scanner
**Date**: 2026-01-18
**Phase**: 0 - Research & Technology Selection

## Overview

This document captures research findings and technology decisions for implementing the YAML file scanner - the first stage of the ArgoCD Application migration pipeline.

## Technology Decisions

### 1. CLI Framework: Typer

**Decision**: Use Typer for CLI interface

**Rationale**:
- Built on top of Click with modern Python type hints
- Automatic help generation from function signatures
- Native support for multiple output formats
- Rich integration for beautiful terminal output
- Excellent error messages out of the box
- Recommended by Python community for modern CLI apps

**Alternatives Considered**:
- **Click**: More verbose, requires decorators for everything. Typer provides better DX with type hints.
- **argparse** (stdlib): Too low-level, requires manual help text, error handling, and validation.
- **Fire**: Too magical, less control over parameter naming and validation.

**Integration**:
```python
import typer
from typing_extensions import Annotated

app = typer.Typer()

@app.command()
def scan(
    input_dir: Annotated[str, typer.Option("--input-dir", "-i", help="Directory to scan")],
    recursive: Annotated[bool, typer.Option("--recursive", "-r", help="Scan recursively")] = False,
    format: Annotated[str, typer.Option("--format", "-f", help="Output format")] = "human",
    verbosity: Annotated[str, typer.Option("--verbosity", "-v", help="Output verbosity")] = "info"
):
    pass
```

### 2. Terminal Output: Rich

**Decision**: Use Rich for human-readable terminal output

**Rationale**:
- Beautiful, colorized terminal output
- Built-in support for tables, progress bars, syntax highlighting
- Excellent error message formatting
- Works seamlessly with Typer
- Handles terminal width detection automatically
- Gracefully degrades in non-TTY environments

**Alternatives Considered**:
- **colorama**: Lower-level, requires manual ANSI code management
- **termcolor**: Limited features compared to Rich
- **Plain print()**: No formatting, poor UX

**Integration**:
```python
from rich.console import Console
from rich.table import Table

console = Console()

# Human-readable output
table = Table(title="Scan Results")
table.add_column("File Path", style="cyan")
for file_path in results:
    table.add_row(file_path)
console.print(table)

# Error output
console.print("[red]Error:[/red] Directory not found", file=sys.stderr)
```

### 3. File System Operations: pathlib

**Decision**: Use pathlib (Python stdlib) for file system operations

**Rationale**:
- Built-in to Python 3.12, no external dependency
- Object-oriented path handling
- Cross-platform path operations
- Clean API for glob patterns, existence checks, permission handling
- Better than os.path for modern Python

**Alternatives Considered**:
- **os + os.path**: Older, more verbose, string-based API
- **glob module**: Limited compared to pathlib's rglob()

**Integration**:
```python
from pathlib import Path

def scan_directory(input_dir: Path, recursive: bool) -> list[Path]:
    if recursive:
        # Recursive glob with filtering
        return [
            p for p in input_dir.rglob("*.[yY][aA][mM][lL]")
            if not any(part.startswith('.') for part in p.parts)
        ]
    else:
        # Non-recursive glob
        return [
            p for p in input_dir.glob("*.[yY][aA][mM][lL]")
        ]
```

### 4. Type Safety: Pydantic

**Decision**: Use Pydantic for ScanResult and ScanOptions data models

**Rationale**:
- Runtime validation + static type checking
- Automatic JSON serialization/deserialization
- Clear error messages for invalid data
- Widely used in Python ecosystem
- Better than TypedDict for this use case (includes validation)

**Alternatives Considered**:
- **dataclasses**: No runtime validation
- **TypedDict**: No runtime validation, harder to serialize
- **attrs**: Less popular, fewer features than Pydantic

**Integration**:
```python
from pydantic import BaseModel, Field, field_validator
from pathlib import Path

class ScanOptions(BaseModel):
    input_dir: Path
    recursive: bool = False
    format: str = "human"  # "human" or "json"
    verbosity: str = "info"  # "quiet", "info", "verbose"

    @field_validator('input_dir')
    @classmethod
    def validate_directory(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"Directory does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Path is not a directory: {v}")
        return v

class ScanResult(BaseModel):
    files: list[Path]
    count: int
    errors: list[str] = Field(default_factory=list)

    def to_json_array(self) -> list[str]:
        """Return simple array of file paths as strings"""
        return [str(f.resolve()) for f in self.files]
```

### 5. Testing: pytest

**Decision**: Use pytest for all testing

**Rationale**:
- De facto standard for Python testing
- Excellent fixture system for setting up test directories
- Parametrized tests for testing multiple scenarios
- Good coverage reporting integration
- Supports both unit and integration tests

**Alternatives Considered**:
- **unittest** (stdlib): More verbose, less Pythonic
- **nose2**: Less maintained than pytest

**Integration**:
```python
import pytest
from pathlib import Path
from scanner.core import scan_directory

@pytest.fixture
def sample_dir(tmp_path):
    """Create a temporary directory with YAML files"""
    (tmp_path / "file1.yaml").touch()
    (tmp_path / "file2.yml").touch()
    (tmp_path / "file3.txt").touch()  # Not YAML
    return tmp_path

def test_scan_finds_yaml_files(sample_dir):
    result = scan_directory(sample_dir, recursive=False)
    assert len(result) == 2
    assert all(f.suffix in ['.yaml', '.yml'] for f in result)
```

### 6. Package Management: UV

**Decision**: Use UV for package management and project setup

**Rationale**:
- Specified in constitution as required package manager
- Extremely fast (Rust-based)
- Compatible with pyproject.toml standard
- Handles virtual environments automatically
- Better dependency resolution than pip

**Integration**:
```toml
# pyproject.toml
[project]
name = "argocd-migrator"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.9.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "mypy>=1.5.0",
    "ruff>=0.1.0",
]

[project.scripts]
argocd-scan = "scanner.cli:app"

[tool.ruff]
line-length = 100
target-version = "py312"
```

## Implementation Patterns

### Pattern 1: Symlink Handling Strategy

**Decision**: Disable symlink following in recursive mode, enable in non-recursive mode

**Rationale**:
- Prevents infinite cycles in recursive traversal
- Clarified in spec: symlinks ignored when `--recursive` flag is set
- pathlib's `rglob()` doesn't follow symlinks by default (Python 3.10+)
- For non-recursive mode, can use `glob()` with `follow_symlinks=True`

**Implementation**:
```python
def scan_directory(input_dir: Path, recursive: bool) -> Iterator[Path]:
    if recursive:
        # rglob doesn't follow symlinks by default in Python 3.10+
        for pattern in ["*.yaml", "*.yml"]:
            for path in input_dir.rglob(pattern):
                # Skip hidden directories
                if not any(part.startswith('.') for part in path.parts):
                    yield path.resolve()
    else:
        # glob can follow symlinks
        for pattern in ["*.yaml", "*.yml"]:
            for path in input_dir.glob(pattern):
                yield path.resolve()
```

### Pattern 2: Hidden Directory Filtering

**Decision**: Filter out hidden directories (starting with `.`) during traversal

**Rationale**:
- Avoids scanning `.git`, `.venv`, `.cache`, etc.
- Specified in FR-014
- Check each part of the path for leading dot

**Implementation**:
```python
def is_hidden(path: Path) -> bool:
    """Check if any part of the path is a hidden directory"""
    return any(part.startswith('.') for part in path.parts)

# Usage in scanner
for path in input_dir.rglob("*.yaml"):
    if not is_hidden(path):
        yield path
```

### Pattern 3: Error Handling with Partial Results

**Decision**: Continue scanning on permission errors, collect both results and errors

**Rationale**:
- FR-019: Output successful files to stdout, errors to stderr, exit code 1
- Allows partial success when some directories are inaccessible
- Better UX than failing completely

**Implementation**:
```python
def scan_directory(input_dir: Path, recursive: bool) -> tuple[list[Path], list[str]]:
    files = []
    errors = []

    try:
        iterator = input_dir.rglob("*.yaml") if recursive else input_dir.glob("*.yaml")
        for path in iterator:
            try:
                if not is_hidden(path):
                    files.append(path.resolve())
            except PermissionError as e:
                errors.append(f"Permission denied: {path}")
            except Exception as e:
                errors.append(f"Error accessing {path}: {str(e)}")
    except PermissionError as e:
        errors.append(f"Permission denied accessing directory: {input_dir}")

    return files, errors
```

### Pattern 4: Output Format Selection

**Decision**: Use format parameter to switch between JSON array and Rich terminal output

**Rationale**:
- FR-015: JSON format outputs simple array of strings
- FR-016: Human format uses Rich for formatting
- Verbosity level affects human format only (JSON is always minimal)

**Implementation**:
```python
def output_results(result: ScanResult, format: str, verbosity: str):
    if format == "json":
        # Simple JSON array to stdout
        import json
        print(json.dumps(result.to_json_array()))
    else:
        # Human-readable with Rich
        if verbosity == "quiet":
            pass  # No output except errors
        elif verbosity == "info":
            console.print(f"Found {result.count} YAML files")
        elif verbosity == "verbose":
            table = Table(title=f"Found {result.count} YAML files")
            table.add_column("File Path", style="cyan")
            for file in result.files:
                table.add_row(str(file))
            console.print(table)
```

## Performance Considerations

### File System Iteration

- Use generator/iterator pattern (`rglob()` returns iterator)
- Don't load all file paths into memory before processing
- Stream results as they're discovered

### Memory Bounds

- For JSON output, must collect all paths (needed for array)
- For human output with verbose mode, collect for table formatting
- Both constrained by number of YAML files found (not total files scanned)
- Acceptable: typical ArgoCD repos have hundreds, not millions of YAML files

### Benchmark Expectations

From SC-002: Must scan 10,000 files in under 5 seconds

- pathlib's rglob is efficient (delegates to OS)
- Filtering is minimal (extension check, hidden dir check)
- No file reading/parsing at this stage
- Should easily meet performance target

## Security Considerations

### Path Traversal Prevention

**Risk**: User provides path like `/`, scanning entire filesystem

**Mitigation**:
- Accept absolute or relative paths
- Resolve to absolute path immediately
- No special handling needed - pathlib handles this safely
- User is responsible for providing sensible input directory

### Permission Handling

**Risk**: Scanner crashes on permission-denied directories

**Mitigation**:
- Wrap file system operations in try/except
- Collect permission errors, continue scanning
- Report errors to stderr
- Exit code 1 if any errors occurred

## Open Questions

None - all technical decisions resolved during research phase.

## Next Steps

Proceed to Phase 1:
1. Create data-model.md with Pydantic model definitions
2. Create contracts/ with CLI interface specification
3. Create quickstart.md with installation and usage guide
