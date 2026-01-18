"""Core data models and scanning logic for YAML file discovery."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, computed_field, field_validator


class ScanOptions(BaseModel):
    """Configuration for YAML file scanning operation."""

    input_dir: Path = Field(..., description="Directory to scan for YAML files")
    recursive: bool = Field(default=False, description="Whether to scan subdirectories recursively")
    format: Literal["json", "human"] = Field(
        default="human",
        description="Output format: 'json' for JSON array, 'human' for formatted terminal output",
    )
    verbosity: Literal["quiet", "info", "verbose"] = Field(
        default="info",
        description=(
            "Output verbosity level: 'quiet' (errors only), 'info' (summary), 'verbose' (detailed)"
        ),
    )

    @field_validator("input_dir")
    @classmethod
    def validate_directory_exists(cls, v: Path) -> Path:
        """Ensure the input directory exists and is a directory."""
        if not v.exists():
            raise ValueError(f"Directory does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Path is not a directory: {v}")
        return v.resolve()  # Convert to absolute path

    model_config = {"arbitrary_types_allowed": True}


class ScanResult(BaseModel):
    """Result of a YAML file scanning operation."""

    files: list[Path] = Field(default_factory=list, description="List of discovered YAML files")
    errors: list[tuple[Path, str]] = Field(
        default_factory=list, description="List of errors encountered during scanning"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def count(self) -> int:
        """Number of files discovered."""
        return len(self.files)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_errors(self) -> bool:
        """Whether any errors were encountered."""
        return len(self.errors) > 0

    def to_json_array(self) -> list[str]:
        """Convert to simple JSON array of file path strings."""
        return [str(f) for f in self.files]

    model_config = {"arbitrary_types_allowed": True}


def scan_directory(options: ScanOptions) -> ScanResult:
    """
    Scan directory for YAML files according to provided options.

    Args:
        options: Configuration for the scan operation

    Returns:
        ScanResult containing discovered files and any errors
    """
    from scanner.filters import is_hidden_directory, is_yaml_file

    result = ScanResult()
    seen_files: set[Path] = set()

    try:
        if options.recursive:
            # Recursive mode: use rglob, skip hidden directories, don't follow symlinks
            for item in options.input_dir.rglob("*"):
                # Skip if any parent directory is hidden
                if any(is_hidden_directory(parent) for parent in item.parents):
                    continue
                # Skip symlinks in recursive mode to prevent cycles
                if item.is_symlink():
                    continue
                if item.is_file() and is_yaml_file(item):
                    resolved = item.resolve()
                    if resolved not in seen_files:
                        seen_files.add(resolved)
                        result.files.append(resolved)
        else:
            # Non-recursive mode: only scan top-level files, follow symlinks
            for item in options.input_dir.iterdir():
                if item.is_file() and is_yaml_file(item):
                    resolved = item.resolve()
                    if resolved not in seen_files:
                        seen_files.add(resolved)
                        result.files.append(resolved)
    except PermissionError as e:
        result.errors.append((options.input_dir, f"Permission denied: {e}"))
    except OSError as e:
        result.errors.append((options.input_dir, f"OS error: {e}"))

    # Sort files for consistent output
    result.files.sort()

    return result
