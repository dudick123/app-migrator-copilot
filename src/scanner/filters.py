"""Filtering utilities for file and directory selection."""

from pathlib import Path


def is_yaml_file(path: Path) -> bool:
    """
    Check if a file has a YAML extension (.yaml or .yml).

    Args:
        path: Path to check

    Returns:
        True if the file has a .yaml or .yml extension
    """
    return path.suffix.lower() in {".yaml", ".yml"}


def is_hidden_directory(path: Path) -> bool:
    """
    Check if a directory is hidden (name starts with a dot).

    Args:
        path: Path to check

    Returns:
        True if the directory name starts with '.'
    """
    return path.name.startswith(".")
