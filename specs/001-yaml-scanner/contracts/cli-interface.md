# CLI Interface Contract: YAML File Scanner

**Feature**: YAML File Scanner
**Date**: 2026-01-18
**Phase**: 1 - Design

## Command Overview

```bash
argocd-scan [OPTIONS]
```

Scan directories for ArgoCD Application YAML files (`.yaml` and `.yml` extensions).

---

## Options

### Required Options

#### `--input-dir`, `-i` (Required)

Directory path to scan for YAML files.

- **Type**: Path (string)
- **Required**: Yes
- **Validation**:
  - Must exist on filesystem
  - Must be a directory (not a file)
  - Can be absolute or relative path (converted to absolute internally)
- **Example**:
  ```bash
  argocd-scan --input-dir /path/to/argocd/apps
  argocd-scan -i ./applications
  ```

---

### Optional Options

#### `--recursive`, `-r` (Optional)

Enable recursive scanning of subdirectories.

- **Type**: Boolean flag
- **Default**: False (non-recursive)
- **Behavior**:
  - When False: Only scan files in the specified directory (no subdirectories)
  - When True: Recursively scan all subdirectories
  - Symlinks are NOT followed when recursive mode is enabled (prevents infinite cycles)
- **Example**:
  ```bash
  argocd-scan --input-dir /apps --recursive
  argocd-scan -i /apps -r
  ```

#### `--format`, `-f` (Optional)

Output format selection.

- **Type**: Choice (enum)
- **Values**: `json`, `human`
- **Default**: `human`
- **Behavior**:
  - `json`: Output simple JSON array of file paths to stdout
  - `human`: Output formatted terminal text with Rich library
- **Example**:
  ```bash
  argocd-scan --input-dir /apps --format json
  argocd-scan -i /apps -f human
  ```

#### `--verbosity`, `-v` (Optional)

Output verbosity level (affects human-readable format only).

- **Type**: Choice (enum)
- **Values**: `quiet`, `info`, `verbose`
- **Default**: `info`
- **Behavior**:
  - `quiet`: Suppress all non-error output (only errors to stderr)
  - `info`: Display summary information (file count, completion message)
  - `verbose`: Display detailed messages (each file discovered, each directory scanned)
  - **Note**: Verbosity has no effect on JSON format (always minimal)
- **Example**:
  ```bash
  argocd-scan --input-dir /apps --verbosity quiet
  argocd-scan -i /apps -v verbose
  ```

#### `--help`, `-h` (Optional)

Display help information and exit.

- **Type**: Boolean flag
- **Behavior**: Prints usage information, parameter descriptions, examples, and exits with code 0
- **Example**:
  ```bash
  argocd-scan --help
  argocd-scan -h
  ```

---

## Output Formats

### JSON Format (`--format json`)

**Stdout**: Simple JSON array of absolute file path strings

```json
[
  "/absolute/path/to/app1.yaml",
  "/absolute/path/to/app2.yml",
  "/absolute/path/to/subdir/app3.yaml"
]
```

**Empty Result**:
```json
[]
```

**Characteristics**:
- Always writes to stdout
- One line, compact JSON
- Absolute paths only
- No metadata (file count, timestamps, etc.)
- Errors written separately to stderr (not included in JSON)

---

### Human-Readable Format (`--format human`)

**Verbosity: quiet**

No output to stdout unless errors occur. Errors written to stderr.

**Verbosity: info** (default)

```
Found 3 YAML files
```

**Verbosity: verbose**

```
╭─────────────────── Found 3 YAML files ───────────────────╮
│ /absolute/path/to/app1.yaml                              │
│ /absolute/path/to/app2.yml                               │
│ /absolute/path/to/subdir/app3.yaml                       │
╰──────────────────────────────────────────────────────────╯
```

**Characteristics**:
- Formatted with Rich library (colors, tables, borders)
- Writes to stdout
- Errors written separately to stderr

---

## Error Handling

### Error Output

**All errors are written to stderr**, never to stdout.

**Error Format (human-readable)**:
```
Error: Directory does not exist: /nonexistent/path
Error: Permission denied: /restricted/directory
```

**Error Format (JSON mode)**:

Errors are still written to stderr in human-readable format, NOT in JSON.
This allows the JSON output on stdout to remain a pure array that can be piped to other tools.

```bash
# stdout (valid JSON):
["/path/app1.yaml"]

# stderr (human-readable errors):
Error: Permission denied: /restricted/dir
```

---

### Exit Codes

| Exit Code | Meaning | Scenarios |
|-----------|---------|-----------|
| `0` | Success | Scan completed successfully (with or without finding files) |
| `1` | Error | Any error occurred (invalid parameters, missing directory, permission errors) |

**Exit Code Behavior**:

- **Exit 0**: Scan completed without errors (even if 0 files found)
  ```bash
  argocd-scan --input-dir /empty/dir
  # stdout: []
  # stderr: (empty)
  # exit code: 0
  ```

- **Exit 1**: Any error occurred during scanning
  ```bash
  argocd-scan --input-dir /nonexistent
  # stdout: (empty)
  # stderr: Error: Directory does not exist: /nonexistent
  # exit code: 1
  ```

- **Exit 1 with partial results**: Some files found but errors occurred
  ```bash
  argocd-scan --input-dir /apps --recursive
  # stdout: ["/apps/accessible/app1.yaml"]
  # stderr: Error: Permission denied: /apps/restricted
  # exit code: 1
  ```

---

## Usage Examples

### Example 1: Basic Scan

```bash
argocd-scan --input-dir ./argocd-applications
```

**Output (info verbosity)**:
```
Found 2 YAML files
```

**Exit Code**: 0

---

### Example 2: Recursive JSON Scan

```bash
argocd-scan --input-dir /apps --recursive --format json
```

**Output (stdout)**:
```json
["/apps/prod/app1.yaml", "/apps/staging/app2.yml", "/apps/dev/app3.yaml"]
```

**Exit Code**: 0

---

### Example 3: Verbose Human Format

```bash
argocd-scan --input-dir /apps --verbosity verbose
```

**Output**:
```
╭──────────────── Found 2 YAML files ────────────────╮
│ /apps/app1.yaml                                    │
│ /apps/app2.yml                                     │
╰────────────────────────────────────────────────────╯
```

**Exit Code**: 0

---

### Example 4: Quiet Mode (No Output)

```bash
argocd-scan --input-dir /apps --verbosity quiet
```

**Output (stdout)**: (empty)
**Output (stderr)**: (empty, unless errors)
**Exit Code**: 0

---

### Example 5: Error Handling

```bash
argocd-scan --input-dir /nonexistent
```

**Output (stdout)**: (empty)
**Output (stderr)**:
```
Error: Directory does not exist: /nonexistent
```

**Exit Code**: 1

---

### Example 6: Permission Errors with Partial Results

```bash
argocd-scan --input-dir /apps --recursive --format json
```

**Output (stdout)**:
```json
["/apps/accessible/app1.yaml", "/apps/accessible/app2.yml"]
```

**Output (stderr)**:
```
Error: Permission denied: /apps/restricted
```

**Exit Code**: 1 (because errors occurred)

---

### Example 7: Pipeline Integration

```bash
# Scan and pipe to next stage
argocd-scan --input-dir /apps --format json | argocd-parse

# Count YAML files
argocd-scan --input-dir /apps --format json | jq 'length'

# Save results to file
argocd-scan --input-dir /apps --format json > discovered-files.json
```

---

## Parameter Validation

### Invalid Input Directory

```bash
argocd-scan --input-dir /path/to/file.txt
```

**Error**:
```
Error: Path is not a directory: /path/to/file.txt
```

**Exit Code**: 1

---

### Invalid Format Option

```bash
argocd-scan --input-dir /apps --format xml
```

**Error**:
```
Error: Invalid value for '--format': 'xml' is not one of 'json', 'human'.
```

**Exit Code**: 1

---

### Invalid Verbosity Option

```bash
argocd-scan --input-dir /apps --verbosity debug
```

**Error**:
```
Error: Invalid value for '--verbosity': 'debug' is not one of 'quiet', 'info', 'verbose'.
```

**Exit Code**: 1

---

### Missing Required Option

```bash
argocd-scan
```

**Error**:
```
Error: Missing option '--input-dir' / '-i'.
```

**Exit Code**: 1

---

## Contract Tests

The following scenarios must be validated with contract tests:

1. **Help Display**: `argocd-scan --help` exits 0 and shows usage
2. **Valid Scan**: `argocd-scan -i /valid/dir` exits 0
3. **JSON Output**: Output is valid JSON array
4. **Human Output**: Output contains "Found X YAML files"
5. **Missing Dir**: Nonexistent directory exits 1 with error
6. **Invalid Format**: Invalid `--format` exits 1 with error
7. **Invalid Verbosity**: Invalid `--verbosity` exits 1 with error
8. **Recursive Flag**: `--recursive` finds files in subdirectories
9. **Non-Recursive Default**: Without `--recursive`, only scans top level
10. **Permission Error**: Inaccessible directory exits 1, error to stderr
11. **Partial Success**: Some accessible files + errors = exit 1, files to stdout, errors to stderr
12. **Empty Directory**: Empty directory exits 0 with empty array/no output

---

## Implementation Notes

- Use Typer for CLI framework (handles parsing, validation, help generation)
- Use Rich for human-readable output formatting
- Ensure stdout contains ONLY the output data (JSON array or formatted text)
- Ensure stderr contains ONLY error messages
- Exit codes must be exactly as specified for proper pipeline integration
