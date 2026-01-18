"""CLI application for YAML file scanner."""

import json
from pathlib import Path
from typing import Annotated, Literal, cast

import typer
from rich.console import Console
from rich.table import Table

from scanner.core import ScanOptions, ScanResult, scan_directory

app = typer.Typer(help="Scan directories for ArgoCD Application YAML files")
console = Console()
error_console = Console(stderr=True)


def format_json_output(result: ScanResult) -> None:
    """Output results as JSON array to stdout."""
    print(json.dumps(result.to_json_array()))


def format_human_output(result: ScanResult, verbosity: str) -> None:
    """Output results in human-readable format using Rich."""
    if verbosity == "quiet":
        # Quiet mode: no output unless errors
        return

    if verbosity == "info":
        # Info mode: summary only
        console.print(f"Found {result.count} YAML files")
    elif verbosity == "verbose":
        # Verbose mode: detailed table with all files
        if result.count == 0:
            console.print("No YAML files found")
        else:
            table = Table(title=f"Found {result.count} YAML files")
            table.add_column("File Path", style="cyan")
            for file_path in result.files:
                table.add_row(str(file_path))
            console.print(table)


@app.command()
def scan(
    input_dir: Annotated[
        Path,
        typer.Option(
            "--input-dir",
            "-i",
            help="Directory to scan for YAML files",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
    recursive: Annotated[
        bool,
        typer.Option(
            "--recursive", "-r", help="Scan subdirectories recursively (symlinks ignored)"
        ),
    ] = False,
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: 'json' for JSON array, 'human' for formatted text",
        ),
    ] = "human",
    verbosity: Annotated[
        str,
        typer.Option(
            "--verbosity",
            "-v",
            help="Output verbosity: 'quiet' (errors only), 'info' (summary), 'verbose' (detailed)",
        ),
    ] = "info",
) -> None:
    """
    Scan directories for ArgoCD Application YAML files.

    Discovers all files with .yaml or .yml extensions in the specified directory.
    """
    # Validate format parameter
    if format not in {"json", "human"}:
        error_console.print(f"[red]Error:[/red] Invalid format '{format}'. Use 'json' or 'human'")
        raise typer.Exit(code=1)

    # Validate verbosity parameter
    if verbosity not in {"quiet", "info", "verbose"}:
        error_console.print(
            f"[red]Error:[/red] Invalid verbosity '{verbosity}'. Use 'quiet', 'info', or 'verbose'"
        )
        raise typer.Exit(code=1)

    try:
        # Create scan options
        options = ScanOptions(
            input_dir=input_dir,
            recursive=recursive,
            format=cast(Literal["json", "human"], format),
            verbosity=cast(Literal["quiet", "info", "verbose"], verbosity),
        )

        # Execute scan
        result = scan_directory(options)

        # Output errors to stderr
        if result.has_errors:
            for error_path, error_msg in result.errors:
                error_console.print(f"[red]Error scanning {error_path}:[/red] {error_msg}")

        # Output results based on format
        if format == "json":
            format_json_output(result)
        else:
            format_human_output(result, verbosity)

        # Exit with appropriate code
        if result.has_errors:
            raise typer.Exit(code=1)

    except ValueError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from e
    except Exception as e:
        error_console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()
