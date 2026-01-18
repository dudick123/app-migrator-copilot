"""Unit tests for filtering utilities."""

from pathlib import Path

from scanner.filters import is_hidden_directory, is_yaml_file


class TestIsYamlFile:
    """Tests for is_yaml_file function."""

    def test_yaml_extension(self, tmp_path: Path) -> None:
        """Test .yaml extension is recognized."""
        file_path = tmp_path / "app.yaml"
        assert is_yaml_file(file_path) is True

    def test_yml_extension(self, tmp_path: Path) -> None:
        """Test .yml extension is recognized."""
        file_path = tmp_path / "app.yml"
        assert is_yaml_file(file_path) is True

    def test_case_insensitive(self, tmp_path: Path) -> None:
        """Test extension matching is case-insensitive."""
        assert is_yaml_file(tmp_path / "app.YAML") is True
        assert is_yaml_file(tmp_path / "app.YML") is True
        assert is_yaml_file(tmp_path / "app.Yaml") is True

    def test_non_yaml_extension(self, tmp_path: Path) -> None:
        """Test non-YAML extensions are rejected."""
        assert is_yaml_file(tmp_path / "file.txt") is False
        assert is_yaml_file(tmp_path / "file.json") is False
        assert is_yaml_file(tmp_path / "file.py") is False


class TestIsHiddenDirectory:
    """Tests for is_hidden_directory function."""

    def test_hidden_directories_skipped(self, tmp_path: Path) -> None:
        """Test that hidden directories are identified."""
        assert is_hidden_directory(tmp_path / ".git") is True
        assert is_hidden_directory(tmp_path / ".cache") is True
        assert is_hidden_directory(tmp_path / ".venv") is True

    def test_non_hidden_directory(self, tmp_path: Path) -> None:
        """Test that non-hidden directories are not identified as hidden."""
        assert is_hidden_directory(tmp_path / "apps") is False
        assert is_hidden_directory(tmp_path / "cluster1") is False
