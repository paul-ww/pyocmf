"""CLI commands for pyocmf."""

from __future__ import annotations

import sys
from typing import Annotated

import typer

from pyocmf.compliance import IssueSeverity
from pyocmf.core.ocmf import OCMF
from pyocmf.exceptions import PyOCMFError

from .display import console, display_compliance_result, display_ocmf_structure, verify_signature
from .utils import InputType, detect_input_type, load_ocmf, load_xml_container


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
        input_type = detect_input_type(ocmf_input)

        # Parse OCMF and extract public key (for XML files)
        if input_type == InputType.XML:
            container = load_xml_container(ocmf_input)
            record = container[0]
            ocmf = record.ocmf
            key_to_use = public_key or (record.public_key.key if record.public_key else None)
        else:
            ocmf = OCMF.from_string(ocmf_input)
            key_to_use = public_key

        if key_to_use:
            verify_signature(ocmf, key_to_use)
        else:
            console.print(
                "[yellow]⚠[/yellow] No public key available - skipping signature verification"
            )

        console.print()
        issues = ocmf.check_eichrecht(errors_only=not verbose)
        display_compliance_result(issues, ocmf.is_eichrecht_compliant)

        if verbose:
            display_ocmf_structure(ocmf)

    except PyOCMFError as e:
        console.print(f"[red]✗[/red] OCMF parsing failed: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] File not found: {e}")
        sys.exit(1)


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
        input_type = detect_input_type(ocmf_input)

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
    """Check Eichrecht regulatory compliance.

    Compliance checking requires transaction pairs (begin + end readings).
    For billing-relevant validation, provide both begin and end OCMF records.
    """
    try:
        ocmf1 = OCMF.from_string(_read_input(input1))

        if input2:
            ocmf2 = OCMF.from_string(_read_input(input2))
            issues = ocmf1.check_eichrecht(other=ocmf2, errors_only=not verbose)
            is_compliant = not any(i.severity == IssueSeverity.ERROR for i in issues)
            label = "transaction pair"
        else:
            console.print(
                "[yellow]ℹ[/yellow] Single OCMF record detected. "
                "For complete Eichrecht compliance validation, "
                "provide both begin and end records:"
            )
            console.print("  [dim]ocmf check <begin-ocmf> <end-ocmf>[/dim]\n")
            issues = ocmf1.check_eichrecht(errors_only=not verbose)
            is_compliant = ocmf1.is_eichrecht_compliant
            label = None

        display_compliance_result(issues, is_compliant, label)

    except PyOCMFError as e:
        console.print(f"[red]✗[/red] OCMF parsing failed: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] File not found: {e}")
        sys.exit(1)


def inspect(
    ocmf_input: Annotated[
        str,
        typer.Argument(help="OCMF string, hex-encoded string, or path to XML file"),
    ],
) -> None:
    """Display parsed OCMF structure."""
    try:
        input_type = detect_input_type(ocmf_input)

        if input_type == InputType.XML:
            _inspect_from_xml(ocmf_input)
        else:
            display_ocmf_structure(OCMF.from_string(ocmf_input))

    except PyOCMFError as e:
        console.print(f"[red]✗[/red] OCMF parsing failed: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] File not found: {e}")
        sys.exit(1)


def _read_input(ocmf_input: str) -> str:
    """Read OCMF data from string or file."""
    ocmf = load_ocmf(ocmf_input)
    return ocmf.to_string()


def _verify_single_ocmf(ocmf: OCMF, verbose: bool, public_key: str | None) -> None:
    if not public_key:
        console.print("[yellow]⚠[/yellow] No public key provided")
        if ocmf.signature.SA:
            console.print("[yellow]ℹ[/yellow] Signature present but not verified")
        if verbose:
            display_ocmf_structure(ocmf)
        return

    verify_signature(ocmf, public_key)

    if verbose:
        display_ocmf_structure(ocmf)


def _verify_from_xml(
    xml_path: str, verbose: bool, all_entries: bool, public_key: str | None
) -> None:
    container = load_xml_container(xml_path)
    records_to_process = container.entries if all_entries else [container[0]]

    console.print(f"[green]✓[/green] Found {len(container)} OCMF record(s) in XML file")

    for i, record in enumerate(records_to_process, 1):
        if len(records_to_process) > 1:
            console.print(f"\n[bold cyan]Entry {i}/{len(records_to_process)}:[/bold cyan]")

        key_to_use = public_key or (record.public_key.key if record.public_key else None)
        _verify_single_ocmf(record.ocmf, verbose, key_to_use)


def _inspect_from_xml(xml_path: str) -> None:
    container = load_xml_container(xml_path)
    console.print(f"Found {len(container)} OCMF record(s) in XML file\n")

    for i, record in enumerate(container.entries, 1):
        if i > 1:
            console.print()
        if len(container) > 1:
            console.print(f"[bold cyan]Entry {i}/{len(container)}:[/bold cyan]")
        display_ocmf_structure(record.ocmf)
