"""Integration tests for recursive directory scanning."""

from pathlib import Path

import pytest

from scanner.core import ScanOptions, scan_directory


@pytest.fixture
def nested_argocd_structure(tmp_path: Path) -> Path:
    """Create a nested ArgoCD directory structure."""
    # Top level
    (tmp_path / "base-app.yaml").write_text("base application")

    # Cluster-specific directories
    cluster1 = tmp_path / "cluster1"
    cluster1.mkdir()
    (cluster1 / "app1.yaml").write_text("cluster1 app")

    cluster2 = tmp_path / "cluster2"
    cluster2.mkdir()
    (cluster2 / "app2.yml").write_text("cluster2 app")

    # Nested environment directories
    prod = cluster1 / "production"
    prod.mkdir()
    (prod / "prod-app.yaml").write_text("production app")

    dev = cluster1 / "development"
    dev.mkdir()
    (dev / "dev-app.yaml").write_text("development app")

    # Hidden directory (should be skipped)
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config.yaml").write_text("git config")

    # Cache directory (should be skipped)
    cache_dir = tmp_path / ".cache"
    cache_dir.mkdir()
    (cache_dir / "cache.yml").write_text("cache file")

    return tmp_path


def test_recursive_scan(nested_argocd_structure: Path) -> None:
    """Test recursive scanning discovers all nested YAML files."""
    options = ScanOptions(input_dir=nested_argocd_structure, recursive=True)
    result = scan_directory(options)

    # Should find: base-app.yaml, app1.yaml, app2.yml, prod-app.yaml, dev-app.yaml
    # Should NOT find: .git/config.yaml, .cache/cache.yml
    assert result.count == 5
    assert result.has_errors is False

    file_names = [f.name for f in result.files]
    assert "base-app.yaml" in file_names
    assert "app1.yaml" in file_names
    assert "app2.yml" in file_names
    assert "prod-app.yaml" in file_names
    assert "dev-app.yaml" in file_names

    # Verify hidden directories are skipped
    file_paths = [str(f) for f in result.files]
    assert not any(".git" in path for path in file_paths)
    assert not any(".cache" in path for path in file_paths)


def test_deep_nesting(tmp_path: Path) -> None:
    """Test scanning deeply nested directory structures."""
    # Create 10+ levels of nesting
    current = tmp_path
    for i in range(12):
        current = current / f"level{i}"
        current.mkdir()
        (current / f"app{i}.yaml").write_text(f"level {i}")

    options = ScanOptions(input_dir=tmp_path, recursive=True)
    result = scan_directory(options)

    # Should find all 12 files regardless of depth
    assert result.count == 12
    assert result.has_errors is False
