<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.1 → 1.1.0 (Architecture section added)
Modified principles: None
Added sections:
  - Architecture: Pipeline Pattern (4-stage pipeline definition)
Removed sections: None
Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ Compatible
  - .specify/templates/spec-template.md: ✅ Compatible
  - .specify/templates/tasks-template.md: ✅ Compatible
Follow-up TODOs: None
==================
-->

# App Migrator Constitution

## Core Principles

### I. CLI-First Design

Every feature MUST be accessible via command-line interface. The CLI is the primary interface for this migration tool.

- All functionality MUST be invokable from the command line
- Input MUST be accepted via arguments, flags, stdin, or configuration files
- Output MUST go to stdout (results) and stderr (errors/diagnostics)
- MUST support both human-readable and JSON output formats via `--json` flag
- Exit codes MUST be meaningful: 0 for success, non-zero for specific failure categories

**Rationale**: CLI tools enable automation, scripting, and integration into CI/CD pipelines. Consistent I/O conventions ensure predictable behavior.

### II. Test Coverage Required

All code MUST have adequate test coverage. Tests validate correctness and prevent regressions.

- All public functions and modules MUST have unit tests
- Integration tests MUST cover critical migration paths
- Contract tests MUST verify external API interactions
- Test coverage MUST be measured and reported
- Tests MUST run in CI before merge

**Rationale**: Migration tools handle critical data transformations. Test coverage ensures reliability and catches regressions before they reach users.

### III. Type Safety

Strict typing MUST be enforced throughout the codebase to catch errors at lint/check time.

- Type checker (pyright or mypy) MUST run in strict mode
- All function signatures MUST have explicit parameter and return type annotations
- No use of `Any` type without explicit justification in comments
- All data structures MUST use typed classes, TypedDict, or Pydantic models
- Type errors MUST block CI builds

**Rationale**: Migrations involve complex data transformations. Type safety prevents runtime errors from incorrect data handling.

### IV. Security-First

Security MUST be considered in all design and implementation decisions.

- User input MUST be validated and sanitized before processing
- Credentials and secrets MUST NOT be logged or exposed in output
- File operations MUST be scoped to prevent path traversal attacks
- Dependencies MUST be audited for known vulnerabilities
- Sensitive operations MUST require explicit confirmation (or `--force` flag)

**Rationale**: Migration tools often handle sensitive data and have elevated permissions. Security failures can cause data breaches or system compromise.

### V. Simplicity and Performance

Code MUST be simple, focused, and performant. Avoid over-engineering.

- Follow YAGNI (You Aren't Gonna Need It) - implement only what is needed now
- Prefer composition over inheritance
- Avoid premature optimization but design for reasonable scale
- Large migrations MUST support progress reporting and resumability
- Memory usage MUST be bounded (streaming over loading entire datasets)
- Performance-critical paths SHOULD be profiled and documented

**Rationale**: Migration tools must handle varying workload sizes reliably. Simple code is easier to maintain and debug. Performance matters for large-scale migrations.

## Architecture: Pipeline Pattern

The tool MUST use a 4-stage pipeline architecture:

1. **Scanner** - Find `*.yaml`/`*.yml` files (recursive option available)
2. **Parser** - Extract fields from valid ArgoCD Applications, skip invalid files
3. **Migrator** - Transform to JSON config (1:1 mapping per Application)
4. **Validator** - Validate output against JSON Schema (Draft7Validator)

### Pipeline Requirements

- Each stage MUST be independently testable
- Each stage MUST have a clear input/output contract
- Stages MUST be composable (output of one feeds input of next)
- Errors in one file MUST NOT halt processing of other files
- Each stage MUST report its progress and any skipped/failed items

## Additional Constraints

### Technology Standards

- **Language**: Python 3.12+
- **Package Manager**: UV
- **CLI Framework**: Typer with Rich for terminal output
- **Parsing**: PyYAML for YAML processing
- **Validation**: jsonschema (Draft7Validator)
- **Linting**: Ruff with strict configuration
- **Type Checking**: pyright or mypy in strict mode

### Security Standards

- All dependencies MUST be reviewed before adoption
- Security scanning MUST run in CI pipeline
- No hardcoded credentials or secrets in source code
- Audit logs MUST be generated for data-modifying operations

### Performance Standards

- CLI commands MUST respond within 500ms for help/version/validation
- Migration operations MUST report progress for operations >5 seconds
- Memory usage MUST NOT exceed 512MB for standard operations
- Large file processing MUST use streaming where possible

## Development Workflow

### Code Review Requirements

- All changes MUST be reviewed before merge
- Reviews MUST verify adherence to constitution principles
- Security-sensitive changes MUST have explicit security review

### Quality Gates

- All tests MUST pass
- Type checking MUST pass with no errors
- Linting MUST pass with no errors
- Security scan MUST pass with no high/critical findings

### Commit Standards

- Commits MUST have meaningful messages describing the change
- Breaking changes MUST be clearly documented
- Each commit SHOULD represent a single logical change

## Governance

This constitution defines the non-negotiable principles and standards for the app-migrator-claude project.

### Authority

- This constitution supersedes conflicting practices or conventions
- Deviations require explicit justification documented in code or PR description
- Principle violations MUST be flagged in code review

### Amendment Process

1. Propose amendment via pull request to this document
2. Document rationale for change
3. Review impact on existing code and templates
4. Update version number according to semantic versioning:
   - **MAJOR**: Removing or redefining principles (backward incompatible)
   - **MINOR**: Adding new principles or sections
   - **PATCH**: Clarifications, wording improvements
5. Update dependent templates if affected

### Compliance

- All PRs MUST pass the Constitution Check in plan-template.md
- Complexity violations MUST be justified in the Complexity Tracking table
- Regular audits SHOULD verify ongoing compliance

**Version**: 1.1.0 | **Ratified**: 2026-01-18 | **Last Amended**: 2026-01-18
