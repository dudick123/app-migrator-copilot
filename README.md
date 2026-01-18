# ArgoCD Application Migrator - YAML Scanner

Stage 1 of the ArgoCD Application migration pipeline: discovers YAML files for processing.

## Features

- 🔍 Discover `.yaml` and `.yml` files in directories
- 🌲 Recursive directory tree scanning
- 📊 Multiple output formats (JSON, human-readable)
- 🎚️ Configurable verbosity levels
- 🔒 Permission error handling
- 🚫 Automatic hidden directory filtering

## Installation

### Prerequisites

- Python 3.12+
- UV package manager

### Install UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Setup

```bash
# Install dependencies
uv sync

# Verify installation
uv run argocd-scan --help
```

## Usage

### Basic Scan

Scan a single directory for YAML files:

```bash
uv run argocd-scan --input-dir ./argocd-applications
```

Output:
```
Found 3 YAML files
```

### Recursive Scan

Scan directory tree recursively:

```bash
uv run argocd-scan --input-dir ./argocd --recursive
```

### JSON Output

Output file paths as JSON array for pipeline processing:

```bash
uv run argocd-scan --input-dir ./argocd --format json
```

Output:
```json
["/path/to/app1.yaml", "/path/to/app2.yml"]
```

### Verbosity Levels

**Quiet** (errors only):
```bash
uv run argocd-scan --input-dir ./argocd --verbosity quiet
```

**Info** (summary, default):
```bash
uv run argocd-scan --input-dir ./argocd --verbosity info
```

**Verbose** (detailed table):
```bash
uv run argocd-scan --input-dir ./argocd --verbosity verbose
```

## Parameters

| Parameter | Short | Type | Default | Description |
|-----------|-------|------|---------|-------------|
| `--input-dir` | `-i` | Path | Required | Directory to scan |
| `--recursive` | `-r` | Flag | False | Enable recursive scanning |
| `--format` | `-f` | Choice | `human` | Output format (`json`, `human`) |
| `--verbosity` | `-v` | Choice | `info` | Verbosity level (`quiet`, `info`, `verbose`) |

## Exit Codes

- `0` - Success (files found or not)
- `1` - Error (invalid parameters, permission denied, path errors)

## Development

### Run Tests

```bash
uv run pytest
```

### Type Checking

```bash
uv run mypy src
```

### Linting

```bash
uv run ruff check src tests
```

## Pipeline Architecture

The YAML scanner is Stage 1 of the 4-stage migration pipeline:

1. **Scanner** (this tool) - Discover YAML files
2. **Parser** - Extract ArgoCD Application fields
3. **Migrator** - Transform to JSON config
4. **Validator** - Validate output against JSON Schema