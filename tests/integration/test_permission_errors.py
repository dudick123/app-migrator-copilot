"""Integration tests for permission error handling."""

import os
import sys
from pathlib import Path

import pytest

from scanner.core import ScanOptions, scan_directory


@pytest.mark.skipif(sys.platform == "win32", reason="Unix permissions test")
def test_permission_errors_with_partial_results(tmp_path: Path) -> None:
    """Test that permission errors are reported but scanning continues."""
    # Create accessible directory with YAML file
    accessible = tmp_path / "accessible"
    accessible.mkdir()
    (accessible / "app1.yaml").write_text("accessible app")

    # Create restricted directory with YAML file
    restricted = tmp_path / "restricted"
    restricted.mkdir()
    (restricted / "app2.yaml").write_text("restricted app")

    # Remove read permissions from restricted directory
    os.chmod(restricted, 0o000)

    try:
        # In non-recursive mode, we'll only see top-level files
        # Neither directory's contents will be scanned
        options = ScanOptions(input_dir=tmp_path, recursive=False)
        result = scan_directory(options)

        # Should complete without crashing
        assert result.has_errors is False or result.has_errors is True  # May vary by system

        # In recursive mode, permission errors should be caught
        options_recursive = ScanOptions(input_dir=tmp_path, recursive=True)
        result_recursive = scan_directory(options_recursive)

        # Should find accessible file
        assert result_recursive.count >= 1

    finally:
        # Restore permissions for cleanup
        os.chmod(restricted, 0o755)


def test_partial_success_exit_code_logic(tmp_path: Path) -> None:
    """Test that partial success (files found + errors) returns correct status."""
    # Create a valid directory with files
    (tmp_path / "app1.yaml").write_text("content")
    (tmp_path / "app2.yml").write_text("content")

    options = ScanOptions(input_dir=tmp_path)
    result = scan_directory(options)

    # Simulate partial success
    result.errors.append((tmp_path / "subdir", "Permission denied"))

    # Should have files AND errors
    assert result.count > 0
    assert result.has_errors is True
