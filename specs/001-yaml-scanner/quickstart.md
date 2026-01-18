# Quickstart Guide: YAML File Scanner

**Feature**: YAML File Scanner
**Date**: 2026-01-18
**Version**: 0.1.0

## Overview

The YAML File Scanner is the first stage of the ArgoCD Application migrator pipeline. It discovers `.yaml` and `.yml` files in specified directories and outputs their paths for further processing.

---

## Installation

### Prerequisites

- Python 3.12 or higher
- UV package manager

### Install UV (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/your-org/argocd-migrator.git
cd argocd-migrator

# Install dependencies with UV
uv sync

# Verify installation
uv run argocd-scan --help
```

---

## Quick Start

### Basic Usage

Scan a single directory for YAML files:

```bash
uv run argocd-scan --input-dir ./argocd-applications
```

**Output**:
```
Found 2 YAML files
```

---

### Recursive Scanning

Scan a directory tree recursively:

```bash
uv run argocd-scan --input-dir ./argocd --recursive
```

**Output**:
```
Found 15 YAML files
```

---

### JSON Output

Output file paths as JSON array:

```bash
uv run argocd-scan --input-dir ./argocd --format json
```

**Output**:
```json
["/Users/you/argocd/app1.yaml", "/Users/you/argocd/app2.yml"]
```

---

### Verbose Output

See detailed information about each discovered file:

```bash
uv run argocd-scan --input-dir ./argocd --verbosity verbose
```

**Output**:
```
╭──────────────── Found 2 YAML files ────────────────╮
│ /Users/you/argocd/app1.yaml                        │
│ /Users/you/argocd/app2.yml                         │
╰────────────────────────────────────────────────────╯
```

---

## Common Use Cases

### Use Case 1: Scan ArgoCD Applications Directory

**Scenario**: You have ArgoCD Applications stored in a `./applications` directory and want to discover all of them.

```bash
uv run argocd-scan --input-dir ./applications --recursive --format json
```

**Result**: JSON array of all YAML file paths, ready to pipe to the next pipeline stage.

---

### Use Case 2: Count YAML Files

**Scenario**: You want to know how many ArgoCD Application files exist in a directory tree.

```bash
# Using jq to count
uv run argocd-scan --input-dir ./apps --recursive --format json | jq 'length'

# Or just use info verbosity (default)
uv run argocd-scan --input-dir ./apps --recursive
```

**Result**:
```
Found 42 YAML files
```

---

### Use Case 3: Save Discovered Files to a List

**Scenario**: You want to save the list of discovered files for later processing.

```bash
uv run argocd-scan --input-dir ./apps --recursive --format json > discovered-files.json
```

**Result**: `discovered-files.json` contains:
```json
["/path/to/app1.yaml", "/path/to/app2.yml", ...]
```

---

### Use Case 4: Quiet Scanning (No Output)

**Scenario**: You only care about the exit code (success/failure) and don't want any output.

```bash
uv run argocd-scan --input-dir ./apps --verbosity quiet

if [ $? -eq 0 ]; then
    echo "Scan completed successfully"
else
    echo "Scan encountered errors"
fi
```

---

### Use Case 5: Handle Permission Errors Gracefully

**Scenario**: You're scanning a directory that may have restricted subdirectories, and you want to get partial results.

```bash
uv run argocd-scan --input-dir /var/argocd --recursive --format json 2> errors.log
```

**Result**:
- **stdout**: JSON array of accessible files
- **errors.log**: Permission error messages
- **Exit code**: 1 (indicating errors occurred)

---

## CLI Reference

### Command

```bash
argocd-scan [OPTIONS]
```

### Required Options

| Option | Short | Description |
|--------|-------|-------------|
| `--input-dir` | `-i` | Directory to scan for YAML files (required) |

### Optional Options

| Option | Short | Values | Default | Description |
|--------|-------|--------|---------|-------------|
| `--recursive` | `-r` | flag | False | Enable recursive subdirectory scanning |
| `--format` | `-f` | `json`, `human` | `human` | Output format |
| `--verbosity` | `-v` | `quiet`, `info`, `verbose` | `info` | Output verbosity level |
| `--help` | `-h` | flag | - | Show help message and exit |

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success (scan completed without errors) |
| `1` | Error (invalid parameters, missing directory, permission errors) |

---

## Examples

### Example 1: Basic Scan (Default Settings)

```bash
uv run argocd-scan --input-dir ./io-artifact-examples/argocd-applications
```

**Expected Output**:
```
Found 2 YAML files
```

**Exit Code**: 0

---

### Example 2: Recursive JSON Scan

```bash
uv run argocd-scan -i ./argocd -r -f json
```

**Expected Output**:
```json
["/Users/you/argocd/prod/app1.yaml", "/Users/you/argocd/staging/app2.yml"]
```

**Exit Code**: 0

---

### Example 3: Verbose Detailed Output

```bash
uv run argocd-scan --input-dir ./apps --verbosity verbose
```

**Expected Output**:
```
╭──────────────── Found 3 YAML files ────────────────╮
│ /Users/you/apps/app1.yaml                          │
│ /Users/you/apps/app2.yml                           │
│ /Users/you/apps/subdir/app3.yaml                   │
╰────────────────────────────────────────────────────╯
```

**Exit Code**: 0

---

### Example 4: Pipeline Integration

```bash
# Discover YAML files and pipe to parser (future stage)
uv run argocd-scan --input-dir ./apps --format json | argocd-parse

# Discover and count
uv run argocd-scan --input-dir ./apps --format json | jq 'length'
# Output: 42

# Discover and filter (only .yaml, not .yml)
uv run argocd-scan --input-dir ./apps --format json | jq '.[] | select(endswith(".yaml"))'
```

---

### Example 5: Error Handling

```bash
# Nonexistent directory
uv run argocd-scan --input-dir /nonexistent/path
```

**Expected Output (stderr)**:
```
Error: Directory does not exist: /nonexistent/path
```

**Exit Code**: 1

---

## Troubleshooting

### Issue: "Command not found: argocd-scan"

**Solution**: Ensure you're using `uv run` to execute the command:

```bash
# Correct
uv run argocd-scan --help

# Incorrect (unless installed globally)
argocd-scan --help
```

---

### Issue: "Directory does not exist"

**Cause**: The specified directory path doesn't exist.

**Solution**:
1. Check the path spelling
2. Use absolute paths if relative paths are failing
3. Verify the directory exists: `ls -la /path/to/directory`

```bash
# Bad (relative path might be wrong)
uv run argocd-scan --input-dir applications

# Good (absolute path)
uv run argocd-scan --input-dir /Users/you/project/applications
```

---

### Issue: "Permission denied" errors

**Cause**: Scanner lacks read permissions for some directories.

**Behavior**: Scanner continues processing accessible directories and outputs partial results with exit code 1.

**Solution**:
- Expected behavior - partial results are valid
- Check permissions: `ls -la /restricted/path`
- Run with appropriate permissions if needed

```bash
# Capture errors separately
uv run argocd-scan --input-dir /apps --recursive --format json 2> errors.log

# Check what errors occurred
cat errors.log
```

---

### Issue: No files found in directory that has YAML files

**Cause**: Files have non-standard extensions or are in hidden directories.

**Solution**:
- Check file extensions: `ls ./directory/*.yaml ./directory/*.yml`
- Scanner only finds `.yaml` and `.yml` extensions
- Scanner skips hidden directories (starting with `.`)

---

### Issue: JSON output is not valid

**Cause**: Output might be mixed with error messages.

**Solution**: Redirect stderr to separate errors from stdout:

```bash
# Good (errors go to stderr, JSON goes to stdout)
uv run argocd-scan --input-dir /apps --format json 2> errors.log > results.json

# Verify JSON is valid
jq '.' results.json
```

---

## Testing Your Setup

### Test 1: Verify Installation

```bash
uv run argocd-scan --help
```

**Expected**: Help message displays without errors.

---

### Test 2: Test with Example Data

```bash
# Scan the included examples
uv run argocd-scan --input-dir ./io-artifact-examples/argocd-applications
```

**Expected**:
```
Found 2 YAML files
```

---

### Test 3: Test JSON Output

```bash
uv run argocd-scan --input-dir ./io-artifact-examples/argocd-applications --format json
```

**Expected**: Valid JSON array with 2 file paths.

---

### Test 4: Test Error Handling

```bash
uv run argocd-scan --input-dir /nonexistent
echo "Exit code: $?"
```

**Expected**:
```
Error: Directory does not exist: /nonexistent
Exit code: 1
```

---

## Next Steps

After scanning YAML files, you can:

1. **Parse the files**: Use the Parser stage (future) to extract ArgoCD Application fields
2. **Migrate to JSON**: Use the Migrator stage (future) to transform to JSON config
3. **Validate output**: Use the Validator stage (future) to ensure JSON schema compliance

**Full Pipeline** (when all stages are implemented):
```bash
uv run argocd-scan --input-dir ./apps --format json | \
uv run argocd-parse | \
uv run argocd-migrate | \
uv run argocd-validate
```

---

## Additional Resources

- **Specification**: See [spec.md](spec.md) for detailed requirements
- **Implementation Plan**: See [plan.md](plan.md) for technical design
- **Data Models**: See [data-model.md](data-model.md) for data structures
- **CLI Contract**: See [contracts/cli-interface.md](contracts/cli-interface.md) for interface details

---

## Support

For issues or questions:
1. Check this quickstart guide
2. Review error messages (always written to stderr)
3. Check exit codes (0 = success, 1 = error)
4. Consult the specification documents in `specs/001-yaml-scanner/`
