# Data Model: YAML File Scanner

**Feature**: YAML File Scanner
**Date**: 2026-01-18
**Phase**: 1 - Design

## Overview

This document defines the data structures used by the YAML file scanner. All models use Pydantic for runtime validation and type safety.

## Core Models

### ScanOptions

Configuration for a scan operation. Validated on construction to ensure input directory exists and is accessible.

```python
from pydantic import BaseModel, Field, field_validator
from pathlib import Path
from typing import Literal

class ScanOptions(BaseModel):
    """Configuration for YAML file scanning operation"""

    input_dir: Path = Field(
        ...,
        description="Directory to scan for YAML files"
    )

    recursive: bool = Field(
        default=False,
        description="Whether to scan subdirectories recursively"
    )

    format: Literal["json", "human"] = Field(
        default="human",
        description="Output format: 'json' for JSON array, 'human' for formatted terminal output"
    )

    verbosity: Literal["quiet", "info", "verbose"] = Field(
        default="info",
        description="Output verbosity level: 'quiet' (errors only), 'info' (summary), 'verbose' (detailed)"
    )

    @field_validator('input_dir')
    @classmethod
    def validate_directory_exists(cls, v: Path) -> Path:
        """Ensure the input directory exists and is a directory"""
        if not v.exists():
            raise ValueError(f"Directory does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Path is not a directory: {v}")
        return v.resolve()  # Convert to absolute path

    class Config:
        # Allow Path objects in JSON serialization
        arbitrary_types_allowed = True
```

**Fields**:
- `input_dir` (Path, required): Absolute path to directory to scan. Validated to exist and be a directory.
- `recursive` (bool, default: False): Enable recursive subdirectory traversal
- `format` (Literal["json", "human"], default: "human"): Output format selection
- `verbosity` (Literal["quiet", "info", "verbose"], default: "info"): Verbosity level for human-readable output

**Validation Rules**:
- `input_dir` must exist on the file system
- `input_dir` must be a directory (not a file)
- Path is automatically resolved to absolute path on validation

**Usage**:
```python
# Valid construction
options = ScanOptions(input_dir=Path("/path/to/argocd/apps"))

# With all parameters
options = ScanOptions(
    input_dir=Path("/path/to/argocd/apps"),
    recursive=True,
    format="json",
    verbosity="verbose"
)

# Invalid - will raise ValidationError
options = ScanOptions(input_dir=Path("/nonexistent"))  # ValueError: Directory does not exist
```

---

### ScanResult

Result of a scan operation, containing discovered files and any errors encountered.

```python
from pydantic import BaseModel, Field, computed_field
from pathlib import Path

class ScanResult(BaseModel):
    """Result of a YAML file scanning operation"""

    files: list[Path] = Field(
        default_factory=list,
        description="List of discovered YAML file paths (absolute paths)"
    )

    errors: list[str] = Field(
        default_factory=list,
        description="List of error messages encountered during scanning (e.g., permission errors)"
    )

    @computed_field
    @property
    def count(self) -> int:
        """Number of YAML files found"""
        return len(self.files)

    @computed_field
    @property
    def has_errors(self) -> bool:
        """Whether any errors were encountered during scanning"""
        return len(self.errors) > 0

    def to_json_array(self) -> list[str]:
        """
        Convert to simple JSON array of file path strings.
        This is the format required by FR-015 for JSON output.

        Returns:
            List of absolute file paths as strings
        """
        return [str(f) for f in self.files]

    class Config:
        arbitrary_types_allowed = True
```

**Fields**:
- `files` (list[Path], default: []): List of absolute paths to discovered YAML files
- `errors` (list[str], default: []): List of error messages encountered during scanning

**Computed Properties**:
- `count` (int): Number of files found (len(files))
- `has_errors` (bool): True if any errors occurred

**Methods**:
- `to_json_array() -> list[str]`: Convert files to simple string array for JSON output

**Usage**:
```python
# Create result
result = ScanResult(
    files=[Path("/path/app1.yaml"), Path("/path/app2.yml")],
    errors=["Permission denied: /restricted/dir"]
)

# Access properties
print(result.count)  # 2
print(result.has_errors)  # True

# Convert to JSON array format
json_array = result.to_json_array()
# ["/ path/app1.yaml", "/path/app2.yml"]
```

---

## Helper Types

### OutputFormat

Type alias for output format parameter.

```python
from typing import Literal

OutputFormat = Literal["json", "human"]
```

**Values**:
- `"json"`: Output simple JSON array of file paths to stdout
- `"human"`: Output formatted terminal text using Rich

---

### VerbosityLevel

Type alias for verbosity level parameter.

```python
from typing import Literal

VerbosityLevel = Literal["quiet", "info", "verbose"]
```

**Values**:
- `"quiet"`: Suppress all non-error output (only errors to stderr)
- `"info"`: Display summary information (file count, completion message)
- `"verbose"`: Display detailed processing messages (each file discovered, each directory scanned)

**Note**: Verbosity only affects human-readable output. JSON format always outputs the minimal array structure regardless of verbosity setting.

---

## Relationships

```
ScanOptions (Input)
    ↓
Scanner Logic
    ↓
ScanResult (Output)
    ├── files: list[Path]
    └── errors: list[str]
```

**Flow**:
1. User provides ScanOptions via CLI parameters
2. Scanner validates and processes options
3. Scanner returns ScanResult with discovered files and any errors
4. Output formatter uses ScanResult to generate stdout/stderr output

---

## Validation Rules Summary

| Field | Required | Type | Constraints |
|-------|----------|------|-------------|
| `ScanOptions.input_dir` | Yes | Path | Must exist, must be directory |
| `ScanOptions.recursive` | No | bool | Default: False |
| `ScanOptions.format` | No | Literal | One of: "json", "human". Default: "human" |
| `ScanOptions.verbosity` | No | Literal | One of: "quiet", "info", "verbose". Default: "info" |
| `ScanResult.files` | No | list[Path] | Default: empty list |
| `ScanResult.errors` | No | list[str] | Default: empty list |

---

## State Transitions

ScanOptions is immutable (no state transitions). Once constructed and validated, options do not change.

ScanResult is built progressively during scanning:

```
Initial State:
    files: []
    errors: []

During Scanning:
    files: [file1, file2, ...]
    errors: [error1, error2, ...]  (if any)

Final State:
    files: [complete list of discovered files]
    errors: [complete list of errors encountered]
```

---

## Examples

### Example 1: Successful Single Directory Scan

```python
options = ScanOptions(input_dir=Path("/argocd/apps"))

result = ScanResult(
    files=[
        Path("/argocd/apps/app1.yaml"),
        Path("/argocd/apps/app2.yml"),
        Path("/argocd/apps/app3.yaml")
    ],
    errors=[]
)

print(result.count)  # 3
print(result.has_errors)  # False
```

### Example 2: Recursive Scan with Permission Errors

```python
options = ScanOptions(
    input_dir=Path("/argocd"),
    recursive=True,
    format="json"
)

result = ScanResult(
    files=[
        Path("/argocd/prod/app1.yaml"),
        Path("/argocd/staging/app2.yml")
    ],
    errors=[
        "Permission denied: /argocd/restricted"
    ]
)

print(result.count)  # 2
print(result.has_errors)  # True
print(result.to_json_array())
# ["/argocd/prod/app1.yaml", "/argocd/staging/app2.yml"]
```

### Example 3: No Files Found

```python
options = ScanOptions(input_dir=Path("/empty/dir"))

result = ScanResult(files=[], errors=[])

print(result.count)  # 0
print(result.has_errors)  # False
print(result.to_json_array())  # []
```

---

## Type Annotations

All functions working with these models should use explicit type annotations:

```python
from pathlib import Path

def scan_directory(options: ScanOptions) -> ScanResult:
    """
    Scan directory for YAML files according to options.

    Args:
        options: Validated scan configuration

    Returns:
        ScanResult containing discovered files and any errors
    """
    ...

def format_output(result: ScanResult, format: OutputFormat, verbosity: VerbosityLevel) -> None:
    """
    Output scan results to stdout in the specified format.

    Args:
        result: Scan result to format
        format: Output format (json or human)
        verbosity: Verbosity level (only affects human format)
    """
    ...
```
