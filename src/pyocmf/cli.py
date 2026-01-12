from __future__ import annotations

import pathlib
import sys
from enum import StrEnum
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pyocmf.compliance import EichrechtIssue, IssueSeverity
from pyocmf.constants import OCMF_PREFIX
from pyocmf.core.ocmf import OCMF
from pyocmf.exceptions import PyOCMFError, SignatureVerificationError
from pyocmf.utils.xml import OcmfContainer, OcmfRecord

CMD = "ocmf"

app = typer.Typer(
    name=CMD,
    help="Verify OCMF signatures and check regulatory compliance",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


class InputType(StrEnum):
    XML = "xml"
    OCMF_STRING = "ocmf_string"


@app.command(name="all")
def all_checks(
    ocmf_input: Annotated[
        str,
        typer.Argument(help="OCMF string, hex-encoded string, or path to XML file"),
    ],
    public_key: Annotated[
        str | None,
        typer.Option("--public-key", "-k", help="Hex-encoded public key"),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show detailed OCMF structure and warnings"),
    ] = False,
) -> None:
    """Run both signature verification and compliance check (default command)."""
    try:
        input_type = _detect_input_type(ocmf_input)

        # Parse OCMF and extract public key (for XML files)
        if input_type == InputType.XML:
            path = pathlib.Path(ocmf_input)
            container = OcmfContainer.from_xml(path)
            record = container[0]
            ocmf = record.ocmf
            key_to_use = public_key or (record.public_key.key if record.public_key else None)
        else:
            ocmf = OCMF.from_string(ocmf_input)
            key_to_use = public_key

        # First: verify signature
        if key_to_use:
            _verify_signature(ocmf, key_to_use)
        else:
            console.print(
                "[yellow]⚠[/yellow] No public key available - skipping signature verification"
            )

        # Second: check compliance
        console.print()  # Add spacing
        issues = ocmf.check_eichrecht(errors_only=not verbose)
        _display_compliance_result(issues, ocmf.is_eichrecht_compliant)

        # Optional: display structure
        if verbose:
            _display_ocmf_structure(ocmf)

    except PyOCMFError as e:
        console.print(f"[red]✗[/red] OCMF parsing failed: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] File not found: {e}")
        sys.exit(1)


@app.command()
def verify(
    ocmf_input: Annotated[
        str,
        typer.Argument(help="OCMF string, hex-encoded string, or path to XML file"),
    ],
    public_key: Annotated[
        str | None,
        typer.Option("--public-key", "-k", help="Hex-encoded public key"),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show detailed OCMF structure"),
    ] = False,
    all_entries: Annotated[
        bool,
        typer.Option("--all", help="Process all entries in XML file"),
    ] = False,
) -> None:
    """Verify cryptographic signature only (requires pyocmf[crypto])."""
    try:
        input_type = _detect_input_type(ocmf_input)

        if input_type == InputType.XML:
            _verify_from_xml(ocmf_input, verbose, all_entries, public_key)
        else:
            _verify_single_ocmf(OCMF.from_string(ocmf_input), verbose, public_key)

    except PyOCMFError as e:
        console.print(f"[red]✗[/red] OCMF parsing failed: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] File not found: {e}")
        sys.exit(1)


@app.command()
def check(
    input1: Annotated[
        str,
        typer.Argument(help="OCMF string, hex-encoded string, or path to XML file"),
    ],
    input2: Annotated[
        str | None,
        typer.Argument(help="Second OCMF for transaction pair (optional)"),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show warnings in addition to errors"),
    ] = False,
) -> None:
    """Check Eichrecht regulatory compliance."""
    try:
        ocmf1 = OCMF.from_string(_read_input(input1))

        if input2:
            ocmf2 = OCMF.from_string(_read_input(input2))
            issues = ocmf1.check_eichrecht(other=ocmf2, errors_only=not verbose)
            is_compliant = not any(i.severity == IssueSeverity.ERROR for i in issues)
            label = "transaction pair"
        else:
            issues = ocmf1.check_eichrecht(errors_only=not verbose)
            is_compliant = ocmf1.is_eichrecht_compliant
            label = None

        _display_compliance_result(issues, is_compliant, label)

    except PyOCMFError as e:
        console.print(f"[red]✗[/red] OCMF parsing failed: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] File not found: {e}")
        sys.exit(1)


@app.command()
def inspect(
    ocmf_input: Annotated[
        str,
        typer.Argument(help="OCMF string, hex-encoded string, or path to XML file"),
    ],
) -> None:
    """Display parsed OCMF structure."""
    try:
        input_type = _detect_input_type(ocmf_input)

        if input_type == InputType.XML:
            _inspect_from_xml(ocmf_input)
        else:
            _display_ocmf_structure(OCMF.from_string(ocmf_input))

    except PyOCMFError as e:
        console.print(f"[red]✗[/red] OCMF parsing failed: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] File not found: {e}")
        sys.exit(1)


def _detect_input_type(ocmf_input: str) -> InputType:
    if ocmf_input.startswith(OCMF_PREFIX):
        return InputType.OCMF_STRING

    try:
        path = pathlib.Path(ocmf_input)
        if path.exists() and path.is_file():
            return InputType.XML
    except (OSError, ValueError):
        pass

    if ocmf_input.endswith(".xml") or "/" in ocmf_input or "\\" in ocmf_input:
        raise FileNotFoundError(ocmf_input)

    return InputType.OCMF_STRING


def _read_input(ocmf_input: str) -> str:
    """Read OCMF data from string or file."""
    input_type = _detect_input_type(ocmf_input)

    if input_type == InputType.XML:
        path = pathlib.Path(ocmf_input)
        container = OcmfContainer.from_xml(path)
        return container[0].ocmf.to_string()

    return ocmf_input


def _verify_signature(ocmf: OCMF, public_key: str) -> None:
    """Verify signature and display results."""
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


def _verify_single_ocmf(ocmf: OCMF, verbose: bool, public_key: str | None) -> None:
    if not public_key:
        console.print("[yellow]⚠[/yellow] No public key provided")
        if ocmf.signature.SA:
            console.print("[yellow]ℹ[/yellow] Signature present but not verified")
        if verbose:
            _display_ocmf_structure(ocmf)
        return

    _verify_signature(ocmf, public_key)

    if verbose:
        _display_ocmf_structure(ocmf)


def _verify_from_xml(
    xml_path: str, verbose: bool, all_entries: bool, public_key: str | None
) -> None:
    path = pathlib.Path(xml_path)
    if not path.exists():
        raise FileNotFoundError(xml_path)

    container = OcmfContainer.from_xml(path)
    records_to_process: list[OcmfRecord] = container.entries if all_entries else [container[0]]

    console.print(f"[green]✓[/green] Found {len(container)} OCMF record(s) in XML file")

    for i, record in enumerate(records_to_process, 1):
        if len(records_to_process) > 1:
            console.print(f"\n[bold cyan]Entry {i}/{len(records_to_process)}:[/bold cyan]")

        key_to_use = public_key or (record.public_key.key if record.public_key else None)
        _verify_single_ocmf(record.ocmf, verbose, key_to_use)


def _display_compliance_result(
    issues: list[EichrechtIssue], is_compliant: bool, label: str | None = None
) -> None:
    """Display compliance check results."""
    label_str = f" {label}" if label else ""

    if not issues:
        console.print(
            f"\n[green]✓[/green] Eichrecht compliance: "
            f"[bold green]COMPLIANT{label_str}[/bold green]"
        )
        return

    errors = [i for i in issues if i.severity == IssueSeverity.ERROR]
    warnings = [i for i in issues if i.severity == IssueSeverity.WARNING]

    if errors:
        console.print(
            f"\n[red]✗[/red] Eichrecht compliance: [bold red]NOT COMPLIANT{label_str}[/bold red]"
        )
    else:
        console.print(
            f"\n[yellow]⚠[/yellow] Eichrecht compliance: "
            f"[bold yellow]COMPLIANT WITH WARNINGS{label_str}[/bold yellow]"
        )

    if errors:
        console.print("\n[bold red]Errors:[/bold red]")
        for issue in errors:
            _display_issue(issue)

    if warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for issue in warnings:
            _display_issue(issue)

    if not is_compliant:
        sys.exit(1)


def _display_issue(issue: EichrechtIssue) -> None:
    """Display a single compliance issue."""
    field_str = f"[{issue.field}] " if issue.field else ""
    console.print(f"  {field_str}{issue.message} ({issue.code.value})")


def _inspect_from_xml(xml_path: str) -> None:
    path = pathlib.Path(xml_path)
    if not path.exists():
        raise FileNotFoundError(xml_path)

    container = OcmfContainer.from_xml(path)
    console.print(f"Found {len(container)} OCMF record(s) in XML file\n")

    for i, record in enumerate(container.entries, 1):
        if i > 1:
            console.print()
        if len(container) > 1:
            console.print(f"[bold cyan]Entry {i}/{len(container)}:[/bold cyan]")
        _display_ocmf_structure(record.ocmf)


def _display_ocmf_structure(ocmf: OCMF) -> None:
    """Display the parsed OCMF structure."""
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
    import sys

    # If no subcommand provided, default to 'all' command
    if len(sys.argv) == 1:
        app(["--help"])
    elif (
        len(sys.argv) >= 2
        and not sys.argv[1].startswith("-")
        and sys.argv[1] not in ["verify", "check", "inspect", "all"]
    ):
        # User provided input without subcommand, use 'all'
        sys.argv.insert(1, "all")

    app()


if __name__ == "__main__":
    main()
