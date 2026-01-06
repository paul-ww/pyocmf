"""CLI for OCMF validation and signature verification."""

from __future__ import annotations

import pathlib
import sys
from enum import StrEnum
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pyocmf.constants import OCMF_PREFIX
from pyocmf.exceptions import PyOCMFError, SignatureVerificationError
from pyocmf.ocmf import OCMF
from pyocmf.utils.xml import OcmfContainer, OcmfRecord

CMD = "ocmf"

app = typer.Typer(
    name=CMD,
    help="Validate and verify Open Charge Metering Format (OCMF) data",
    add_completion=False,
)
console = Console()


class InputType(StrEnum):
    """Type of OCMF input."""

    XML = "xml"
    OCMF_STRING = "ocmf_string"


@app.command()
def validate(
    ocmf_input: Annotated[
        str,
        typer.Argument(
            help="OCMF string, hex-encoded string, or path to XML file",
        ),
    ],
    public_key: Annotated[
        str | None,
        typer.Option(
            "--public-key",
            "-k",
            help="Hex-encoded public key for signature verification",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed OCMF structure",
        ),
    ] = False,
    all_entries: Annotated[
        bool,
        typer.Option(
            "--all",
            help="Process all OCMF entries in XML file (default: first only)",
        ),
    ] = False,
) -> None:
    """Validate an OCMF string and optionally verify its signature.

    The input format is auto-detected:
    - If input is an existing file path, it's treated as XML
    - If input starts with "OCMF|", it's treated as an OCMF string
    - Otherwise, it's treated as hex-encoded OCMF

    Examples:
        # Validate OCMF string
        ocmf 'OCMF|{...}|{...}'

        # Validate and verify signature
        ocmf 'OCMF|{...}|{...}' --public-key 3059301306...

        # Validate hex-encoded OCMF
        ocmf 4f434d467c7b...

        # Validate from XML file (auto-extracts public key)
        ocmf charging_session.xml

        # Validate all entries in XML file
        ocmf charging_session.xml --all
    """
    try:
        # Auto-detect input type
        input_type = _detect_input_type(ocmf_input)

        if input_type == InputType.XML:
            _validate_from_xml(ocmf_input, verbose, all_entries)
        else:  # InputType.OCMF_STRING (handles both plain and hex-encoded)
            _validate_single_ocmf(OCMF.from_string(ocmf_input), verbose, public_key)

    except PyOCMFError as e:
        console.print(f"[red]✗[/red] OCMF validation failed: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] File not found: {e}")
        sys.exit(1)


def _detect_input_type(ocmf_input: str) -> InputType:
    """Detect the type of input provided.

    Returns:
        InputType.XML if input is an existing file path
        InputType.OCMF_STRING otherwise (handles both plain and hex-encoded)

    Raises:
        FileNotFoundError: If input looks like a file path but doesn't exist
    """
    # Check if it's an OCMF string first
    if ocmf_input.startswith(OCMF_PREFIX):
        return InputType.OCMF_STRING

    # Try to treat as a file path
    try:
        path = pathlib.Path(ocmf_input)
        if path.exists() and path.is_file():
            return InputType.XML
    except (OSError, ValueError):
        # OSError for paths that are too long, ValueError for invalid path characters
        # If pathlib can't handle it, treat as OCMF string
        pass

    # Check if it looks like a file path (has file extension or path separators)
    if ocmf_input.endswith(".xml") or "/" in ocmf_input or "\\" in ocmf_input:
        raise FileNotFoundError(ocmf_input)

    # Fall back to OCMF string processing
    return InputType.OCMF_STRING


def _validate_single_ocmf(ocmf: OCMF, verbose: bool, public_key: str | None) -> None:
    """Validate and optionally verify a single OCMF object."""
    console.print("[green]✓[/green] Successfully parsed OCMF string")
    console.print("[green]✓[/green] OCMF validation passed")

    if verbose:
        _display_ocmf_details(ocmf)

    if public_key:
        _verify_signature(ocmf, public_key)
    elif ocmf.signature.SA:
        console.print(
            "\n[yellow]ℹ[/yellow] Signature present but not verified (use --public-key to verify)"
        )


def _validate_from_xml(xml_path: str, verbose: bool, all_entries: bool) -> None:
    """Validate OCMF data from XML file."""
    path = pathlib.Path(xml_path)
    if not path.exists():
        msg = f"XML file not found: {xml_path}"
        raise FileNotFoundError(msg)

    container = OcmfContainer.from_xml(path)

    number_of_records = len(container)
    record_string = "record" if number_of_records == 1 else "records"
    console.print(f"[green]✓[/green] Found {number_of_records} OCMF {record_string} in XML file")

    records_to_process: list[OcmfRecord] = container.entries if all_entries else [container[0]]

    for i, record in enumerate(records_to_process, 1):
        if len(records_to_process) > 1:
            console.print(f"\n[bold cyan]Entry {i}/{len(records_to_process)}:[/bold cyan]")

        console.print("[green]✓[/green] Successfully parsed OCMF string")
        console.print("[green]✓[/green] OCMF validation passed")

        if verbose:
            _display_ocmf_details(record.ocmf)

        # Auto-verify with public key from XML if available
        if record.public_key:
            _verify_signature(record.ocmf, record.public_key.key)
        elif record.ocmf.signature.SA:
            console.print("\n[yellow]ℹ[/yellow] Signature present but no public key found in XML")


def _verify_signature(ocmf: OCMF, public_key: str) -> None:
    """Verify OCMF signature with the provided public key."""
    try:
        is_valid = ocmf.verify_signature(public_key)

        if is_valid:
            console.print(
                "\n[green]✓[/green] Signature verification: [bold green]VALID[/bold green]"
            )

            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_row("Algorithm:", ocmf.signature.SA or "N/A")
            table.add_row("Encoding:", ocmf.signature.SE or "hex")

            console.print(table)
        else:
            console.print("\n[red]✗[/red] Signature verification: [bold red]INVALID[/bold red]")
            console.print("[yellow]⚠[/yellow] The signature does not match the payload")
            sys.exit(1)

    except SignatureVerificationError as e:
        console.print(f"\n[red]✗[/red] Signature verification failed: {e}")
        sys.exit(1)
    except ImportError as e:
        console.print(f"\n[red]✗[/red] {e}")
        console.print("[yellow]ℹ[/yellow] Install with: pip install pyocmf[crypto]")
        sys.exit(1)


def _display_ocmf_details(ocmf: OCMF) -> None:
    """Display detailed OCMF structure."""
    console.print("\n[bold]OCMF Structure:[/bold]")

    console.print("\n[bold cyan]Payload:[/bold cyan]")
    payload_table = Table(show_header=False, box=None, padding=(0, 2))
    payload_table.add_row("Format Version:", ocmf.payload.FV)
    payload_table.add_row("Gateway ID:", ocmf.payload.GI)
    payload_table.add_row("Gateway Serial:", ocmf.payload.GS)
    payload_table.add_row("Pagination:", ocmf.payload.PG)

    console.print(payload_table)

    if ocmf.payload.RD:
        console.print(f"\n[bold cyan]Readings:[/bold cyan] {len(ocmf.payload.RD)} reading(s)")
        for i, reading in enumerate(ocmf.payload.RD, 1):
            reading_table = Table(show_header=False, box=None, padding=(0, 2))
            reading_table.add_row("Time:", str(reading.TM))
            reading_table.add_row("Type:", reading.TX)
            reading_table.add_row("Value:", f"{reading.RV} {reading.RU}")
            reading_table.add_row("Identifier:", str(reading.RI) if reading.RI else "N/A")
            reading_table.add_row("Status:", reading.ST)

            console.print(Panel(reading_table, title=f"Reading {i}", border_style="cyan"))

    console.print("\n[bold cyan]Signature:[/bold cyan]")
    sig_table = Table(show_header=False, box=None, padding=(0, 2))
    sig_table.add_row("Algorithm:", ocmf.signature.SA or "N/A")
    sig_table.add_row("Encoding:", ocmf.signature.SE or "hex")
    sig_table.add_row(
        "Data:",
        f"{ocmf.signature.SD[:32]}..." if len(ocmf.signature.SD) > 32 else ocmf.signature.SD,
    )

    console.print(sig_table)


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
