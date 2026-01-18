"""Unit tests for scanner core functionality."""

from pathlib import Path

import pytest

from scanner.core import ScanOptions, ScanResult, scan_directory


@pytest.fixture
def temp_yaml_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with sample YAML files."""
    # Create some YAML files
    (tmp_path / "app1.yaml").write_text("apiVersion: v1\nkind: Application")
    (tmp_path / "app2.yml").write_text("apiVersion: v1\nkind: Application")
    (tmp_path / "config.txt").write_text("Not a YAML file")
    return tmp_path


@pytest.fixture
def nested_yaml_dir(tmp_path: Path) -> Path:
    """Create a nested directory structure with YAML files."""
    # Top level
    (tmp_path / "app1.yaml").write_text("top level")

    # Subdirectory
    subdir = tmp_path / "cluster1"
    subdir.mkdir()
    (subdir / "app2.yaml").write_text("level 1")

    # Deeper subdirectory
    deeper = subdir / "production"
    deeper.mkdir()
    (deeper / "app3.yml").write_text("level 2")

    # Hidden directory (should be skipped)
    hidden = tmp_path / ".git"
    hidden.mkdir()
    (hidden / "config.yaml").write_text("hidden")

    return tmp_path


class TestScanOptions:
    """Tests for ScanOptions model."""

    def test_valid_options(self, temp_yaml_dir: Path) -> None:
        """Test creating valid scan options."""
        options = ScanOptions(input_dir=temp_yaml_dir)
        assert options.input_dir == temp_yaml_dir.resolve()
        assert options.recursive is False
        assert options.format == "human"
        assert options.verbosity == "info"

    def test_directory_not_exists(self, tmp_path: Path) -> None:
        """Test that nonexistent directory raises ValueError."""
        nonexistent = tmp_path / "does_not_exist"
        with pytest.raises(ValueError, match="does not exist"):
            ScanOptions(input_dir=nonexistent)

    def test_path_is_file_not_directory(self, tmp_path: Path) -> None:
        """Test that file path raises ValueError."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")
        with pytest.raises(ValueError, match="not a directory"):
            ScanOptions(input_dir=file_path)


class TestScanResult:
    """Tests for ScanResult model."""

    def test_empty_result(self) -> None:
        """Test empty scan result."""
        result = ScanResult()
        assert result.count == 0
        assert result.has_errors is False
        assert result.to_json_array() == []

    def test_result_with_files(self, temp_yaml_dir: Path) -> None:
        """Test scan result with files."""
        result = ScanResult(files=[temp_yaml_dir / "app1.yaml", temp_yaml_dir / "app2.yml"])
        assert result.count == 2
        assert result.has_errors is False
        assert len(result.to_json_array()) == 2

    def test_result_with_errors(self, temp_yaml_dir: Path) -> None:
        """Test scan result with errors."""
        result = ScanResult(errors=[(temp_yaml_dir, "Permission denied")])
        assert result.count == 0
        assert result.has_errors is True


class TestScanDirectory:
    """Tests for scan_directory function."""

    def test_scan_single_directory(self, temp_yaml_dir: Path) -> None:
        """Test scanning a single directory."""
        options = ScanOptions(input_dir=temp_yaml_dir)
        result = scan_directory(options)

        assert result.count == 2
        assert any("app1.yaml" in str(f) for f in result.files)
        assert any("app2.yml" in str(f) for f in result.files)
        assert not any("config.txt" in str(f) for f in result.files)

    def test_both_extensions_discovered(self, temp_yaml_dir: Path) -> None:
        """Test that both .yaml and .yml extensions are discovered."""
        options = ScanOptions(input_dir=temp_yaml_dir)
        result = scan_directory(options)

        yaml_files = [f for f in result.files if f.suffix == ".yaml"]
        yml_files = [f for f in result.files if f.suffix == ".yml"]

        assert len(yaml_files) > 0
        assert len(yml_files) > 0

    def test_empty_directory_returns_empty_list(self, tmp_path: Path) -> None:
        """Test scanning empty directory."""
        options = ScanOptions(input_dir=tmp_path)
        result = scan_directory(options)

        assert result.count == 0
        assert result.files == []
        assert result.has_errors is False

    def test_recursive_scan_multiple_depths(self, nested_yaml_dir: Path) -> None:
        """Test recursive scan discovers files at multiple depths."""
        options = ScanOptions(input_dir=nested_yaml_dir, recursive=True)
        result = scan_directory(options)

        # Should find app1.yaml (top), app2.yaml (level 1), app3.yml (level 2)
        # Should NOT find .git/config.yaml (hidden directory)
        assert result.count == 3
        assert any("app1.yaml" in str(f) for f in result.files)
        assert any("app2.yaml" in str(f) for f in result.files)
        assert any("app3.yml" in str(f) for f in result.files)
        assert not any(".git" in str(f) for f in result.files)

    def test_non_recursive_default_only_top_level(self, nested_yaml_dir: Path) -> None:
        """Test non-recursive mode only scans top level."""
        options = ScanOptions(input_dir=nested_yaml_dir, recursive=False)
        result = scan_directory(options)

        # Should only find app1.yaml at top level
        assert result.count == 1
        assert any("app1.yaml" in str(f) for f in result.files)
        assert not any("app2.yaml" in str(f) for f in result.files)
        assert not any("app3.yml" in str(f) for f in result.files)

    def test_recursive_ignores_symlinks(self, tmp_path: Path) -> None:
        """Test that symlinks are ignored in recursive mode."""
        # Create directory with YAML file
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        (real_dir / "app.yaml").write_text("content")

        # Create symlink to the directory
        link_dir = tmp_path / "link"
        link_dir.symlink_to(real_dir)

        options = ScanOptions(input_dir=tmp_path, recursive=True)
        result = scan_directory(options)

        # Should only find the file once (in real_dir, not via symlink)
        assert result.count == 1
