"""CLI for OCMF validation and signature verification."""

from __future__ import annotations

import pathlib
import sys
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pyocmf.exceptions import PyOCMFError, SignatureVerificationError
from pyocmf.ocmf import OCMF
from pyocmf.utils.xml import extract_ocmf_data_from_file

app = typer.Typer(
    name="ocmf",
    help="Validate and verify Open Charge Metering Format (OCMF) data",
    add_completion=False,
)
console = Console()


@app.command()
def validate(
    ocmf_input: Annotated[
        str,
        typer.Argument(
            help="OCMF string or path to XML file (format: OCMF|{payload}|{signature})",
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
    hex_encoded: Annotated[
        bool,
        typer.Option(
            "--hex",
            help="Treat input as hex-encoded OCMF string",
        ),
    ] = False,
    xml_file: Annotated[
        bool,
        typer.Option(
            "--xml",
            help="Treat input as path to XML file containing OCMF data",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed OCMF structure",
        ),
    ] = False,
    verify_all: Annotated[
        bool,
        typer.Option(
            "--all",
            help="Process all OCMF entries in XML file (default: first only)",
        ),
    ] = False,
) -> None:
    """Validate an OCMF string and optionally verify its signature.

    Examples:
        # Validate OCMF string
        ocmf 'OCMF|{...}|{...}'

        # Validate and verify signature
        ocmf 'OCMF|{...}|{...}' --public-key 3059301306...

        # Validate hex-encoded OCMF
        ocmf 4f434d467c7b... --hex

        # Validate from XML file (auto-extracts public key)
        ocmf charging_session.xml --xml

        # Validate all entries in XML file
        ocmf charging_session.xml --xml --all
    """
    try:
        if xml_file:
            _validate_from_xml(ocmf_input, verbose, verify_all)
        elif hex_encoded:
            ocmf = OCMF.from_hex(ocmf_input)
            console.print("[green]✓[/green] Successfully parsed hex-encoded OCMF string")
            console.print("[green]✓[/green] OCMF validation passed")

            if verbose:
                _display_ocmf_details(ocmf)

            if public_key:
                _verify_signature(ocmf, public_key)
            elif ocmf.signature.SA:
                console.print(
                    "\n[yellow]ℹ[/yellow] Signature present but not verified "
                    "(use --public-key to verify)"
                )
        else:
            ocmf = OCMF.from_string(ocmf_input)
            console.print("[green]✓[/green] Successfully parsed OCMF string")
            console.print("[green]✓[/green] OCMF validation passed")

            if verbose:
                _display_ocmf_details(ocmf)

            if public_key:
                _verify_signature(ocmf, public_key)
            elif ocmf.signature.SA:
                console.print(
                    "\n[yellow]ℹ[/yellow] Signature present but not verified "
                    "(use --public-key to verify)"
                )

    except PyOCMFError as e:
        console.print(f"[red]✗[/red] OCMF validation failed: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] File not found: {e}")
        sys.exit(1)


def _validate_from_xml(xml_path: str, verbose: bool, verify_all: bool) -> None:
    """Validate OCMF data from XML file."""
    path = pathlib.Path(xml_path)
    if not path.exists():
        msg = f"XML file not found: {xml_path}"
        raise FileNotFoundError(msg)

    ocmf_data_list = extract_ocmf_data_from_file(path)

    if not ocmf_data_list:
        console.print("[red]✗[/red] No OCMF data found in XML file")
        sys.exit(1)

    console.print(f"[green]✓[/green] Found {len(ocmf_data_list)} OCMF entry(ies) in XML file")

    entries_to_process = ocmf_data_list if verify_all else [ocmf_data_list[0]]

    for i, ocmf_data in enumerate(entries_to_process, 1):
        if len(entries_to_process) > 1:
            console.print(f"\n[bold cyan]Entry {i}/{len(entries_to_process)}:[/bold cyan]")

        ocmf = OCMF.from_string(ocmf_data.ocmf_string)
        console.print("[green]✓[/green] Successfully parsed OCMF string")
        console.print("[green]✓[/green] OCMF validation passed")

        if verbose:
            _display_ocmf_details(ocmf)

        # Auto-verify with public key from XML if available
        if ocmf_data.public_key:
            _verify_signature(ocmf, ocmf_data.public_key.key_hex)
        elif ocmf.signature.SA:
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
            reading_table.add_row("Identifier:", reading.RI)
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
