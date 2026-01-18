# Feature Specification: YAML File Scanner

**Feature Branch**: `001-yaml-scanner`
**Created**: 2026-01-18
**Status**: Draft
**Input**: User description: "YAML file scanner stage - discover and enumerate YAML/YML files for ArgoCD Application migration"

## Clarifications

### Session 2026-01-18

- Q: When the scanner encounters a symbolic link cycle (e.g., dir1/link → dir2, dir2/link → dir1), what should happen? → A: Disable symlink following when recursive mode is enabled to avoid cycles entirely
- Q: What is the primary output format when the scanner completes successfully? → A: Both JSON and human-readable formats (user can choose via parameter)
- Q: What should the JSON output structure look like when using the JSON format? → A: Simple array of file paths
- Q: What exit codes should the scanner return? → A: Simple binary: 0 for success (files found or not), 1 for any error
- Q: When permission errors occur during scanning but some files are successfully found, how should errors be communicated? → A: Errors to stderr, results to stdout, exit code 1 (standard Unix pattern)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scan Single Directory (Priority: P1)

As a DevOps engineer, I want to scan a single directory for YAML files so that I can quickly discover ArgoCD Application manifests in a known location.

**Why this priority**: This is the most common use case - users typically know where their ArgoCD manifests are stored and want to scan that specific directory.

**Independent Test**: Can be fully tested by pointing the scanner at a directory containing YAML files and verifying all files are discovered.

**Acceptance Scenarios**:

1. **Given** a directory containing 5 YAML files, **When** I run the scanner on that directory with the input directory parameter, **Then** I receive a list of all 5 file paths.
2. **Given** a directory containing files with `.yaml` and `.yml` extensions, **When** I run the scanner, **Then** both extension types are discovered.
3. **Given** a directory containing no YAML files, **When** I run the scanner, **Then** I receive an empty list with no errors.
4. **Given** I want to understand how to use the scanner, **When** I invoke the help parameter, **Then** I see usage information including all available parameters and their descriptions.
5. **Given** a directory with 10 YAML files, **When** I run the scanner with informational output verbosity, **Then** I see a summary showing "10 files found" without individual file details.
6. **Given** a directory with 3 YAML files, **When** I run the scanner with verbose output verbosity, **Then** I see detailed messages for each file discovered and each directory scanned.
7. **Given** a directory with YAML files, **When** I run the scanner with no output verbosity, **Then** I see no messages unless an error occurs.
8. **Given** a directory with 3 YAML files, **When** I run the scanner with JSON format selected, **Then** I receive a JSON array containing exactly 3 file path strings (e.g., `["/path/to/file1.yaml", "/path/to/file2.yml", "/path/to/file3.yaml"]`).
9. **Given** the scanner completes successfully (with or without finding files), **When** I check the exit code, **Then** it is 0.
10. **Given** the scanner encounters any error (invalid parameters, missing directory, permission error), **When** I check the exit code, **Then** it is 1.

---

### User Story 2 - Recursive Directory Scan (Priority: P2)

As a DevOps engineer, I want to recursively scan a directory tree for YAML files so that I can discover all ArgoCD manifests across a complex repository structure.

**Why this priority**: Many organizations store ArgoCD manifests in nested directory structures (e.g., by environment, cluster, or application). Recursive scanning is essential for comprehensive discovery.

**Independent Test**: Can be fully tested by creating a nested directory structure with YAML files at various depths and verifying all are discovered.

**Acceptance Scenarios**:

1. **Given** a directory tree with YAML files at depth levels 1, 2, and 3, **When** I run the scanner with the recursive parameter enabled, **Then** all files at all depths are discovered.
2. **Given** the recursive parameter is not specified (default off), **When** I run the scanner on a directory with subdirectories, **Then** only top-level YAML files are returned.
3. **Given** a deeply nested structure (10+ levels), **When** I run the scanner with the recursive parameter enabled, **Then** all YAML files are discovered regardless of depth.
4. **Given** a directory tree containing hidden directories (`.git`, `.cache`) with YAML files inside them, **When** I run the scanner with the recursive parameter enabled, **Then** those hidden directories are skipped and their YAML files are not discovered.
5. **Given** a directory tree with some subdirectories lacking read permissions but other subdirectories accessible, **When** I run the scanner with the recursive parameter enabled, **Then** accessible files are written to stdout, permission errors are written to stderr, and the exit code is 1.

---

### Edge Cases

- What happens when no input directory parameter is provided? Scanner writes an error to stderr indicating the input directory is required and exits with code 1.
- What happens when an invalid output format is specified? Scanner writes an error to stderr listing the valid format options (JSON, human-readable) and exits with code 1.
- What happens when an invalid output verbosity level is specified? Scanner writes an error to stderr listing the valid verbosity options and exits with code 1.
- What happens when no YAML files are found and JSON format is selected? Scanner outputs an empty JSON array to stdout: `[]` and exits with code 0.
- What happens when a directory path does not exist? Scanner writes a clear error message to stderr indicating the path was not found and exits with code 1.
- What happens when a directory is not readable due to permissions? Scanner writes a permission error to stderr for that directory, continues scanning accessible paths if any, outputs successfully found files to stdout, and exits with code 1.
- What happens when symbolic links point to YAML files in non-recursive mode? Scanner follows symlinks and includes the linked files.
- What happens when symbolic links are encountered in recursive mode? Scanner ignores symbolic links entirely to prevent infinite cycles.
- What happens when a file has a YAML extension but is not valid YAML? Scanner includes the file (validation is the Parser stage's responsibility).
- What happens when the same file is reachable via multiple symlink paths in non-recursive mode? Scanner reports each unique file only once (deduplicated by resolved path).
- What happens when hidden directories (starting with `.`) are encountered? Scanner skips hidden directories entirely and does not traverse into them.

## Requirements *(mandatory)*

### Functional Requirements

#### CLI Parameters

- **FR-001**: Scanner MUST provide a help parameter that displays usage information and all available parameters.
- **FR-002**: Scanner MUST accept an input directory parameter to specify the directory to scan.
- **FR-003**: Scanner MUST accept an output format parameter to choose between JSON and human-readable formats (default: human-readable).
- **FR-004**: Scanner MUST accept an output verbosity parameter with three levels:
  - **No output**: Suppress all non-error messages (only errors displayed)
  - **Informational**: Display summary messages (files found count, scan completion)
  - **Verbose**: Display detailed processing messages (each file discovered, each directory scanned, YAML validation status)
- **FR-005**: Scanner MUST accept a recursive parameter to enable/disable subdirectory traversal (disabled by default).

#### Scanning Behavior

- **FR-006**: Scanner MUST discover all files with `.yaml` extension in the specified directory.
- **FR-007**: Scanner MUST discover all files with `.yml` extension in the specified directory.
- **FR-008**: Scanner MUST return the absolute path for each discovered file.
- **FR-009**: Scanner MUST report an error when the specified path does not exist.
- **FR-010**: Scanner MUST report an error when the specified path is not a directory.
- **FR-011**: Scanner MUST handle permission errors gracefully, reporting inaccessible paths without crashing.
- **FR-012**: Scanner MUST follow symbolic links when discovering files in non-recursive mode. When recursive mode is enabled, symbolic links MUST NOT be followed to avoid infinite cycles.
- **FR-013**: Scanner MUST deduplicate files reachable via multiple paths (using resolved absolute path) when operating in non-recursive mode.
- **FR-014**: Scanner MUST skip hidden directories (directories whose names start with `.`) during traversal.

#### Output Format

- **FR-015**: When JSON format is selected, scanner MUST output a simple JSON array of file path strings (e.g., `["path1", "path2", "path3"]`) to stdout.
- **FR-016**: When human-readable format is selected, scanner MUST output file paths in a clear, readable format with appropriate summary information based on verbosity level to stdout.
- **FR-017**: Scanner MUST write all error messages to stderr (not stdout).
- **FR-018**: Scanner MUST return exit code 0 on successful completion (regardless of whether files were found) and exit code 1 for any error condition (invalid parameters, path errors, permission errors).
- **FR-019**: When errors occur during scanning but some files are successfully found, scanner MUST output successfully found files to stdout, write error messages to stderr, and return exit code 1.

### Key Entities

- **ScanResult**: Represents the output of a scan operation. Contains: list of discovered file paths, count of files found, count of directories scanned, list of any errors encountered (path + error message).
- **ScanOptions**: Configuration for a scan operation. Contains: input directory path (required), output format (JSON / human-readable, default: human-readable), recursive flag (boolean, default: false), output verbosity level (no output / informational / verbose, default: informational). Note: symlinks are followed only when recursive is false.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Scanner discovers 100% of YAML/YML files in a test directory structure with known file counts.
- **SC-002**: Scanner completes scanning of 10,000 files in under 5 seconds on standard hardware.
- **SC-003**: Scanner correctly handles and reports 100% of permission errors without crashing.
- **SC-004**: Users can understand scanner output and identify discovered files within 10 seconds of viewing results.
- **SC-005**: Users can successfully invoke the help parameter and understand all available options within 30 seconds.

## Assumptions

- Users have read access to the majority of directories they intend to scan.
- The file system being scanned is a local or network-mounted file system (not cloud object storage).
- YAML files use standard `.yaml` or `.yml` extensions (non-standard extensions like `.yamlx` are out of scope).
- Hidden directories (starting with `.`) typically contain tool/system files not relevant to ArgoCD manifests (e.g., `.git`, `.venv`, `.cache`).
- Symbolic links in recursive mode are less common for ArgoCD manifest organization and can be safely ignored to prevent cycle complications.
