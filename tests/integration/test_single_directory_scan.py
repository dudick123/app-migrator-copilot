"""Integration tests for single directory scanning."""

from pathlib import Path

import pytest

from scanner.core import ScanOptions, scan_directory


@pytest.fixture
def sample_argocd_dir(tmp_path: Path) -> Path:
    """Create a sample ArgoCD applications directory."""
    (tmp_path / "app-frontend.yaml").write_text("""
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: frontend
spec:
  source:
    repoURL: https://github.com/example/frontend
    """)

    (tmp_path / "app-backend.yml").write_text("""
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: backend
spec:
  source:
    repoURL: https://github.com/example/backend
    """)

    (tmp_path / "README.md").write_text("# ArgoCD Applications")
    (tmp_path / "values.yaml").write_text("# Helm values")

    return tmp_path


def test_single_directory_scan(sample_argocd_dir: Path) -> None:
    """Test scanning a single directory with multiple YAML files."""
    options = ScanOptions(input_dir=sample_argocd_dir, recursive=False)
    result = scan_directory(options)

    # Should find all YAML/YML files (app-frontend.yaml, app-backend.yml, values.yaml)
    assert result.count == 3
    assert result.has_errors is False

    # Check specific files
    file_names = [f.name for f in result.files]
    assert "app-frontend.yaml" in file_names
    assert "app-backend.yml" in file_names
    assert "values.yaml" in file_names
    assert "README.md" not in file_names


def test_json_output_format(sample_argocd_dir: Path) -> None:
    """Test JSON output format produces correct structure."""
    options = ScanOptions(input_dir=sample_argocd_dir, format="json")
    result = scan_directory(options)

    json_array = result.to_json_array()
    assert isinstance(json_array, list)
    assert len(json_array) == 3
    assert all(isinstance(path, str) for path in json_array)
    assert all(path.endswith((".yaml", ".yml")) for path in json_array)
